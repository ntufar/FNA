"""
DocumentProcessor service for FNA Platform.

Orchestrates document parsing, sentiment analysis, and data processing workflows.
Coordinates between file processing, iXBRL parsing, and sentiment analysis services.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
import numpy as np

from ..core.config import get_settings
from ..core.exceptions import (
    FileProcessingError, ModelInferenceError, log_performance, 
    ValidationError, DatabaseError
)
from ..models import (
    FinancialReport, NarrativeAnalysis, NarrativeEmbedding, 
    ProcessingStatus, FileFormat, SectionType
)

from .sentiment_analyzer import SentimentAnalyzer, SentimentAnalysisResult
from .sec_downloader import SECDownloader
from .ixbrl_parser import get_ixbrl_parser, extract_financial_metrics, iXBRLParsingError
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class ProcessingStep(Enum):
    """Enumeration of document processing steps."""
    VALIDATION = "VALIDATION"
    TEXT_EXTRACTION = "TEXT_EXTRACTION"
    IXBRL_PARSING = "IXBRL_PARSING"
    SENTIMENT_ANALYSIS = "SENTIMENT_ANALYSIS"
    EMBEDDING_GENERATION = "EMBEDDING_GENERATION"
    DATABASE_STORAGE = "DATABASE_STORAGE"
    COMPLETED = "COMPLETED"


class ProcessingResult:
    """Container for document processing results."""
    
    def __init__(self):
        self.steps_completed: List[ProcessingStep] = []
        self.processing_time_seconds: int = 0
        self.narrative_analysis: Optional[NarrativeAnalysis] = None
        self.financial_metrics: Optional[Dict[str, Any]] = None
        self.embeddings: List[NarrativeEmbedding] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def add_step(self, step: ProcessingStep):
        """Mark a processing step as completed."""
        if step not in self.steps_completed:
            self.steps_completed.append(step)
    
    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)
        logger.error(f"Processing error: {error}")
    
    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)
        logger.warning(f"Processing warning: {warning}")
    
    def is_successful(self) -> bool:
        """Check if processing completed successfully."""
        return (ProcessingStep.COMPLETED in self.steps_completed and 
                len(self.errors) == 0)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of processing results."""
        return {
            'successful': self.is_successful(),
            'steps_completed': [step.value for step in self.steps_completed],
            'processing_time_seconds': self.processing_time_seconds,
            'has_narrative_analysis': self.narrative_analysis is not None,
            'has_financial_metrics': self.financial_metrics is not None,
            'embedding_count': len(self.embeddings),
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': self.errors,
            'warnings': self.warnings
        }


class DocumentProcessor:
    """
    Document processor that orchestrates the complete analysis workflow.
    
    Coordinates between file processing, iXBRL parsing, sentiment analysis,
    and embedding generation to produce comprehensive analysis results.
    """
    
    def __init__(self):
        """Initialize the document processor with required services."""
        self.settings = get_settings()
        
        # Initialize services
        self.sentiment_analyzer = SentimentAnalyzer()
        self.sec_downloader = SECDownloader()
        self.embedding_service = EmbeddingService()
        
        # Processing configuration
        self.max_processing_time = 300  # 5 minutes maximum
        self.supported_formats = {FileFormat.PDF, FileFormat.HTML, FileFormat.TXT, FileFormat.IXBRL}
        
        logger.info("DocumentProcessor initialized with all services")
    
    @log_performance("document_processing")
    def process_financial_report(
        self,
        financial_report: FinancialReport,
        include_embeddings: bool = True,
        force_reprocess: bool = False
    ) -> ProcessingResult:
        """
        Process a financial report through the complete analysis pipeline.
        
        Args:
            financial_report: FinancialReport model instance
            include_embeddings: Whether to generate embeddings
            force_reprocess: Force reprocessing even if already analyzed
            
        Returns:
            ProcessingResult: Complete processing results
        """
        start_time = time.time()
        result = ProcessingResult()
        
        try:
            logger.info(f"Starting document processing for report {financial_report.id}")
            
            # Check if already processed
            if not force_reprocess and financial_report.is_completed:
                existing_analysis = financial_report.latest_analysis
                if existing_analysis:
                    result.narrative_analysis = existing_analysis
                    result.add_warning("Report already processed, returning existing analysis")
                    return result
            
            # Mark as processing
            financial_report.set_processing()
            
            # Step 1: Validation
            self._validate_report(financial_report, result)
            result.add_step(ProcessingStep.VALIDATION)
            
            # Step 2: Extract text content
            text_sections = self._extract_text_content(financial_report, result)
            result.add_step(ProcessingStep.TEXT_EXTRACTION)
            
            # Step 3: Parse iXBRL if available
            financial_metrics = None
            if financial_report.file_format == FileFormat.IXBRL:
                financial_metrics = self._parse_ixbrl_content(financial_report, result)
                result.add_step(ProcessingStep.IXBRL_PARSING)
            
            # Step 4: Perform sentiment analysis
            narrative_analysis = self._perform_sentiment_analysis(
                financial_report, text_sections, financial_metrics, result
            )
            result.narrative_analysis = narrative_analysis
            result.financial_metrics = financial_metrics
            result.add_step(ProcessingStep.SENTIMENT_ANALYSIS)
            
            # Step 5: Generate embeddings if requested
            if include_embeddings and narrative_analysis:
                embeddings = self._generate_embeddings(narrative_analysis, text_sections, result)
                result.embeddings = embeddings
                result.add_step(ProcessingStep.EMBEDDING_GENERATION)
            
            # Step 6: Update report status
            financial_report.set_completed()
            result.add_step(ProcessingStep.DATABASE_STORAGE)
            
            # Mark as completed
            result.add_step(ProcessingStep.COMPLETED)
            result.processing_time_seconds = int(time.time() - start_time)
            
            logger.info(f"Document processing completed successfully in {result.processing_time_seconds}s")
            
            return result
            
        except Exception as e:
            processing_time = int(time.time() - start_time)
            result.processing_time_seconds = processing_time
            result.add_error(f"Processing failed after {processing_time}s: {str(e)}")
            
            # Mark report as failed
            financial_report.set_failed()
            
            logger.error(f"Document processing failed for report {financial_report.id}: {e}")
            return result
    
    def _validate_report(self, financial_report: FinancialReport, result: ProcessingResult):
        """
        Validate financial report for processing.
        
        Args:
            financial_report: Report to validate
            result: Processing result to update
            
        Raises:
            ValidationError: If validation fails
        """
        # Check file exists
        file_path = Path(financial_report.file_path)
        if not file_path.exists():
            raise ValidationError(f"Report file not found: {file_path}")
        
        # Check file size
        if not financial_report.validate_file_size():
            raise ValidationError("File size exceeds maximum allowed size")
        
        # Check file format is supported
        if financial_report.file_format not in self.supported_formats:
            result.add_warning(f"File format {financial_report.file_format.value} may not be fully supported")
        
        # Check fiscal period format
        if not financial_report.validate_fiscal_period():
            result.add_warning("Invalid fiscal period format")
        
        logger.debug(f"Report validation passed for {financial_report.id}")
    
    def _extract_text_content(
        self, 
        financial_report: FinancialReport, 
        result: ProcessingResult
    ) -> Dict[str, str]:
        """
        Extract text content from financial report file.
        
        Args:
            financial_report: Report to process
            result: Processing result to update
            
        Returns:
            dict: Extracted text sections
        """
        try:
            file_path = Path(financial_report.file_path)
            
            if financial_report.file_format == FileFormat.TXT:
                # Read plain text file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {'full_document': content}
            
            elif financial_report.file_format in [FileFormat.HTML, FileFormat.IXBRL]:
                # Parse HTML/iXBRL content
                return self._extract_html_text(file_path)
            
            elif financial_report.file_format == FileFormat.PDF:
                # Extract text from PDF (placeholder - would need PDF library)
                result.add_warning("PDF text extraction not yet implemented")
                return {'full_document': 'PDF content extraction pending'}
            
            else:
                result.add_warning(f"Text extraction not implemented for {financial_report.file_format.value}")
                return {'full_document': 'Generic content'}
                
        except Exception as e:
            raise FileProcessingError(f"Failed to extract text content: {str(e)}", financial_report.file_path)
    
    def _extract_html_text(self, file_path: Path) -> Dict[str, str]:
        """
        Extract text content from HTML/iXBRL files.
        
        Args:
            file_path: Path to HTML file
            
        Returns:
            dict: Extracted text sections
        """
        try:
            # Basic HTML text extraction (could be enhanced with BeautifulSoup)
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Remove HTML tags (basic approach)
            import re
            text_content = re.sub(r'<[^>]+>', ' ', html_content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            # Try to identify sections (basic approach)
            sections = {'full_document': text_content}
            
            # Look for common section headers
            md_a_pattern = r'(?i)(management.{0,50}discussion.{0,50}analysis|md&a)'
            if re.search(md_a_pattern, text_content):
                # Extract MD&A section (simplified)
                sections['mda'] = text_content  # Placeholder - would need better extraction
            
            return sections
            
        except Exception as e:
            raise FileProcessingError(f"Failed to extract HTML text: {str(e)}", str(file_path))
    
    def _parse_ixbrl_content(
        self, 
        financial_report: FinancialReport, 
        result: ProcessingResult
    ) -> Optional[Dict[str, Any]]:
        """
        Parse iXBRL content to extract structured financial data.
        
        Args:
            financial_report: Report with iXBRL content
            result: Processing result to update
            
        Returns:
            dict: Financial metrics or None if parsing fails
        """
        try:
            logger.info(f"Parsing iXBRL content for report {financial_report.id}")
            
            file_path = Path(financial_report.file_path)
            financial_metrics = extract_financial_metrics(file_path)
            
            if financial_metrics.get('metadata', {}).get('parsing_success'):
                logger.info("iXBRL parsing successful")
                return financial_metrics
            else:
                result.add_warning("iXBRL parsing failed, proceeding without structured data")
                return None
                
        except iXBRLParsingError as e:
            result.add_warning(f"iXBRL parsing error: {str(e)}")
            return None
        except Exception as e:
            result.add_warning(f"Unexpected iXBRL parsing error: {str(e)}")
            return None
    
    def _perform_sentiment_analysis(
        self,
        financial_report: FinancialReport,
        text_sections: Dict[str, str],
        financial_metrics: Optional[Dict[str, Any]],
        result: ProcessingResult
    ) -> NarrativeAnalysis:
        """
        Perform sentiment analysis on text content.
        
        Args:
            financial_report: Report being processed
            text_sections: Extracted text content
            financial_metrics: Optional financial data from iXBRL
            result: Processing result to update
            
        Returns:
            NarrativeAnalysis: Analysis results
            
        Raises:
            ModelInferenceError: If sentiment analysis fails
        """
        try:
            logger.info(f"Performing sentiment analysis for report {financial_report.id}")
            
            # Combine text sections for analysis
            combined_text = ""
            narrative_sections = {}
            
            for section_name, text_content in text_sections.items():
                if text_content and len(text_content.strip()) > 100:  # Skip very short sections
                    combined_text += f"\n{text_content}"
                    narrative_sections[section_name] = text_content[:500]  # Store preview
            
            if not combined_text.strip():
                raise ModelInferenceError("No substantial text content found for analysis")
            
            # Perform sentiment analysis
            analysis_result = self.sentiment_analyzer.analyze_text(
                combined_text,
                section_type="financial_report"
            )
            
            # Create NarrativeAnalysis model
            narrative_analysis = self.sentiment_analyzer.create_analysis_record(
                analysis_result,
                financial_report.id,
                financial_metrics
            )
            
            # Update narrative sections with extracted content
            narrative_analysis.narrative_sections = narrative_sections
            
            logger.info(
                f"Sentiment analysis completed: "
                f"optimism={narrative_analysis.optimism_score:.2f}, "
                f"risk={narrative_analysis.risk_score:.2f}, "
                f"uncertainty={narrative_analysis.uncertainty_score:.2f}"
            )
            
            return narrative_analysis
            
        except ModelInferenceError as e:
            result.add_error(f"Sentiment analysis failed: {str(e)}")
            raise
        except Exception as e:
            result.add_error(f"Unexpected sentiment analysis error: {str(e)}")
            raise ModelInferenceError(f"Sentiment analysis failed: {str(e)}")
    
    def _generate_embeddings(
        self,
        narrative_analysis: NarrativeAnalysis,
        text_sections: Dict[str, str],
        result: ProcessingResult
    ) -> List[NarrativeEmbedding]:
        """
        Generate embeddings for text sections.
        
        Args:
            narrative_analysis: Analysis containing the text
            text_sections: Text content by section
            result: Processing result to update
            
        Returns:
            list: Generated embedding records
        """
        try:
            logger.info(f"Generating embeddings for analysis {narrative_analysis.id}")
            
            # Ensure embedding model is loaded
            if not self.embedding_service.is_loaded():
                logger.info("Loading embedding model...")
                if not self.embedding_service.load_model():
                    result.add_warning("Failed to load embedding model, skipping embeddings")
                    return []
            
            embeddings = []
            
            for section_name, text_content in text_sections.items():
                if text_content and len(text_content.strip()) > 50:  # Skip very short sections
                    try:
                        # Determine section type
                        section_type = self._map_section_type(section_name)
                        
                        # Generate embedding (encode_texts returns 2D array, get first row and convert to list)
                        embedding_array = self.embedding_service.encode_texts(text_content)
                        embedding_vector = embedding_array[0].tolist()
                        
                        # Create embedding record
                        embedding = NarrativeEmbedding.create_from_text(
                            analysis_id=narrative_analysis.id,
                            section_type=section_type,
                            text_content=text_content,
                            embedding_vector=embedding_vector,
                            chunk_index=len(embeddings)
                        )
                        
                        embeddings.append(embedding)
                        
                    except Exception as e:
                        result.add_warning(f"Failed to generate embedding for section {section_name}: {e}")
                        continue
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            result.add_warning(f"Embedding generation error: {str(e)}")
            return []
    
    def _map_section_type(self, section_name: str) -> SectionType:
        """
        Map section name to SectionType enum.
        
        Args:
            section_name: Name of the document section
            
        Returns:
            SectionType: Mapped section type
        """
        section_lower = section_name.lower()
        
        if 'mda' in section_lower or 'management' in section_lower or 'discussion' in section_lower:
            return SectionType.MD_A
        elif 'ceo' in section_lower or 'letter' in section_lower or 'message' in section_lower:
            return SectionType.CEO_LETTER
        elif 'risk' in section_lower:
            return SectionType.RISK_FACTORS
        else:
            return SectionType.OTHER
    
    def process_batch_reports(
        self,
        financial_reports: List[FinancialReport],
        max_concurrent: int = None
    ) -> List[ProcessingResult]:
        """
        Process multiple financial reports in batch.
        
        Args:
            financial_reports: List of reports to process
            max_concurrent: Maximum concurrent processing (default from config)
            
        Returns:
            list: Processing results for each report
        """
        if max_concurrent is None:
            max_concurrent = self.settings.max_concurrent_analyses
        
        logger.info(f"Processing batch of {len(financial_reports)} reports with max_concurrent={max_concurrent}")
        
        results = []
        
        # Process reports (simple sequential for now - could be enhanced with async)
        for i, report in enumerate(financial_reports):
            try:
                logger.info(f"Processing report {i+1}/{len(financial_reports)}: {report.id}")
                result = self.process_financial_report(report)
                results.append(result)
                
                # Check if we should stop on failures
                if not result.is_successful():
                    logger.warning(f"Report {report.id} processing failed, continuing with next")
                
            except Exception as e:
                logger.error(f"Batch processing error for report {report.id}: {e}")
                error_result = ProcessingResult()
                error_result.add_error(f"Batch processing failed: {str(e)}")
                results.append(error_result)
        
        successful_count = sum(1 for r in results if r.is_successful())
        logger.info(f"Batch processing completed: {successful_count}/{len(results)} successful")
        
        return results
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check of all services.
        
        Returns:
            dict: Health status of all components
        """
        try:
            health_status = {
                'status': 'healthy',
                'components': {},
                'overall_healthy': True
            }
            
            # Check sentiment analyzer
            sentiment_health = self.sentiment_analyzer.health_check()
            health_status['components']['sentiment_analyzer'] = sentiment_health
            if sentiment_health.get('status') != 'healthy':
                health_status['overall_healthy'] = False
            
            # Check SEC downloader
            sec_health = self.sec_downloader.health_check()
            health_status['components']['sec_downloader'] = sec_health
            if sec_health.get('status') != 'healthy':
                health_status['overall_healthy'] = False
            
            # Check iXBRL parser
            ixbrl_parser = get_ixbrl_parser()
            ixbrl_health = ixbrl_parser.health_check()
            health_status['components']['ixbrl_parser'] = ixbrl_health
            if ixbrl_health.get('status') != 'healthy':
                health_status['overall_healthy'] = False
            
            # Check embedding service
            embedding_health = self.embedding_service.health_check()
            health_status['components']['embedding_service'] = embedding_health
            if embedding_health.get('status') != 'healthy':
                health_status['overall_healthy'] = False
            
            # Update overall status
            if not health_status['overall_healthy']:
                health_status['status'] = 'degraded'
            
            return health_status
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'overall_healthy': False
            }
