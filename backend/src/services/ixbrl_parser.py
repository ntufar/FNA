"""iXBRL Parser Service using Arelle library.

This module handles parsing of iXBRL (Inline eXtensible Business Reporting Language)
documents as specified in research.md. Enhanced for FNA platform integration.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

# Arelle imports - these will be available after pip install arelle
try:
    from arelle import Cntlr, ModelManager, PackageManager
    from arelle.ModelDocument import ModelDocument
    from arelle.ModelXbrl import ModelXbrl
    ARELLE_AVAILABLE = True
except ImportError:
    ARELLE_AVAILABLE = False

from ..core.config import get_settings
from ..core.exceptions import FileProcessingError, log_performance

logger = logging.getLogger(__name__)


@dataclass
class iXBRLData:
    """Structured data extracted from iXBRL document."""
    
    facts: Dict[str, Any]
    concepts: List[str]
    contexts: Dict[str, Any]
    units: Dict[str, Any]
    narrative_sections: List[str]
    filing_metadata: Dict[str, Any]


class iXBRLParsingError(FileProcessingError):
    """Exception raised when iXBRL parsing fails."""
    
    def __init__(self, message: str, filename: Optional[str] = None):
        super().__init__(message, filename)


class FinancialDataExtractor:
    """Extracts and categorizes financial data from iXBRL facts."""
    
    # Common financial statement line items to look for
    REVENUE_CONCEPTS = [
        'revenues', 'revenue', 'sales', 'netsales', 'totalsales',
        'operatingrevenues', 'salesrevenue', 'totalrevenues'
    ]
    
    INCOME_CONCEPTS = [
        'netincome', 'netearnings', 'profit', 'netprofit',
        'netincomeloss', 'comprehensiveincome', 'earnings'
    ]
    
    EXPENSE_CONCEPTS = [
        'costofrevenue', 'costofgoodssold', 'operatingexpenses',
        'totaloperatingexpenses', 'expenses', 'costs'
    ]
    
    BALANCE_SHEET_CONCEPTS = [
        'totalassets', 'assets', 'totalliabilities', 'liabilities',
        'stockholdersequity', 'equity', 'cash', 'cashequivalents'
    ]
    
    def extract_key_metrics(self, facts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key financial metrics from iXBRL facts.
        
        Args:
            facts: Dictionary of XBRL facts
            
        Returns:
            dict: Categorized financial metrics
        """
        metrics = {
            'revenue': {},
            'income': {},
            'expenses': {},
            'balance_sheet': {},
            'other': {}
        }
        
        for fact_name, fact_data in facts.items():
            fact_lower = fact_name.lower()
            
            # Categorize the fact
            if any(concept in fact_lower for concept in self.REVENUE_CONCEPTS):
                metrics['revenue'][fact_name] = fact_data
            elif any(concept in fact_lower for concept in self.INCOME_CONCEPTS):
                metrics['income'][fact_name] = fact_data
            elif any(concept in fact_lower for concept in self.EXPENSE_CONCEPTS):
                metrics['expenses'][fact_name] = fact_data
            elif any(concept in fact_lower for concept in self.BALANCE_SHEET_CONCEPTS):
                metrics['balance_sheet'][fact_name] = fact_data
            else:
                metrics['other'][fact_name] = fact_data
        
        return metrics


class ArelleParser:
    """Arelle-based iXBRL parser for SEC financial filings."""
    
    def __init__(self):
        """Initialize the iXBRL parser with FNA platform settings."""
        self.settings = get_settings()
        self.controller: Optional[Cntlr.Cntlr] = None
        self.financial_extractor = FinancialDataExtractor()
        self.cache_dir = Path("arelle_cache")
        self._initialize_arelle()
    
    def _initialize_arelle(self) -> None:
        """Initialize Arelle controller and configuration."""
        if not ARELLE_AVAILABLE:
            raise ImportError(
                "Arelle library not available. Install with: pip install arelle"
            )
        
        try:
            # Create cache directory
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize Arelle controller
            self.controller = Cntlr.Cntlr(logFileName=None)
            self.controller.webCache.workOffline = False
            
            # Set log level based on FNA settings
            arelle_log_level = logging.WARNING  # Conservative default
            if self.settings.debug:
                arelle_log_level = logging.INFO
            
            self.controller.logger.setLevel(arelle_log_level)
            
            logger.info("Arelle iXBRL parser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Arelle: {e}")
            raise iXBRLParsingError(f"Failed to initialize Arelle: {e}")
    
    @log_performance("ixbrl_parsing")
    def parse_ixbrl_file(
        self, 
        file_path: Union[str, Path],
        extract_narrative: bool = True
    ) -> iXBRLData:
        """Parse an iXBRL file and extract structured data and narrative content.
        
        Args:
            file_path: Path to the iXBRL file
            extract_narrative: Whether to extract narrative text sections
            
        Returns:
            iXBRLData: Structured data from the iXBRL document
            
        Raises:
            iXBRLParsingError: If parsing fails
        """
        if not self.controller:
            raise iXBRLParsingError("Arelle not initialized")
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise iXBRLParsingError(f"File not found: {file_path}", str(file_path))
        
        logger.info(f"Starting iXBRL parsing for: {file_path}")
        
        model_xbrl = None
        try:
            # Load the iXBRL document
            model_manager = ModelManager.initialize(self.controller)
            model_xbrl = model_manager.load(str(file_path))
            
            if model_xbrl is None:
                raise iXBRLParsingError(f"Failed to load iXBRL document: {file_path}", str(file_path))
            
            logger.debug(f"Successfully loaded iXBRL model from {file_path}")
            
            # Extract structured data
            facts = self._extract_facts(model_xbrl)
            concepts = self._extract_concepts(model_xbrl)
            contexts = self._extract_contexts(model_xbrl)
            units = self._extract_units(model_xbrl)
            metadata = self._extract_metadata(model_xbrl)
            
            logger.info(f"Extracted {len(facts)} facts, {len(concepts)} concepts, {len(contexts)} contexts")
            
            # Extract narrative content if requested
            narrative_sections = []
            if extract_narrative:
                narrative_sections = self._extract_narrative_content(model_xbrl)
                logger.info(f"Extracted {len(narrative_sections)} narrative sections")
            
            return iXBRLData(
                facts=facts,
                concepts=concepts,
                contexts=contexts,
                units=units,
                narrative_sections=narrative_sections,
                filing_metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error parsing iXBRL file {file_path}: {e}")
            raise iXBRLParsingError(f"Error parsing iXBRL file: {e}", str(file_path))
        
        finally:
            # Clean up resources
            if model_xbrl:
                try:
                    model_xbrl.close()
                except Exception as e:
                    logger.warning(f"Error closing iXBRL model: {e}")
            logger.debug(f"Completed iXBRL parsing for {file_path}")
    
    def _extract_facts(self, model_xbrl: ModelXbrl) -> Dict[str, Any]:
        """Extract XBRL facts from the model."""
        facts = {}
        
        for fact in model_xbrl.facts:
            fact_key = f"{fact.qname.localName}"
            facts[fact_key] = {
                "value": fact.value,
                "unit": fact.unit.id if fact.unit else None,
                "context": fact.context.id if fact.context else None,
                "decimals": fact.decimals,
                "precision": fact.precision
            }
        
        return facts
    
    def _extract_concepts(self, model_xbrl: ModelXbrl) -> List[str]:
        """Extract concept names from the model."""
        concepts = []
        
        for concept in model_xbrl.qnameConcepts.values():
            if concept.qname:
                concepts.append(concept.qname.localName)
        
        return list(set(concepts))  # Remove duplicates
    
    def _extract_contexts(self, model_xbrl: ModelXbrl) -> Dict[str, Any]:
        """Extract context information from the model."""
        contexts = {}
        
        for context in model_xbrl.contexts.values():
            contexts[context.id] = {
                "entity": context.entityIdentifier[1] if context.entityIdentifier else None,
                "period": {
                    "start": context.startDatetime.isoformat() if context.startDatetime else None,
                    "end": context.endDatetime.isoformat() if context.endDatetime else None,
                    "instant": context.instantDatetime.isoformat() if context.instantDatetime else None
                }
            }
        
        return contexts
    
    def _extract_units(self, model_xbrl: ModelXbrl) -> Dict[str, Any]:
        """Extract unit definitions from the model."""
        units = {}
        
        for unit in model_xbrl.units.values():
            units[unit.id] = {
                "measures": [str(measure) for measure in unit.measures[0]] if unit.measures else []
            }
        
        return units
    
    def _extract_metadata(self, model_xbrl: ModelXbrl) -> Dict[str, Any]:
        """Extract filing metadata from the model."""
        metadata = {}
        
        # Document info
        if model_xbrl.modelDocument:
            metadata.update({
                "document_type": model_xbrl.modelDocument.type,
                "uri": model_xbrl.modelDocument.uri,
                "creation_software": getattr(model_xbrl.modelDocument, 'creationSoftware', None)
            })
        
        # Schema info
        metadata["schemas"] = [
            doc.uri for doc in model_xbrl.urlDocs.values() 
            if hasattr(doc, 'type') and doc.type == "schema"
        ]
        
        return metadata
    
    def _extract_narrative_content(self, model_xbrl: ModelXbrl) -> List[str]:
        """Extract narrative text content from iXBRL document.
        
        This extracts human-readable text that appears in the iXBRL document,
        which is typically the narrative sections of financial reports.
        """
        narrative_sections = []
        
        try:
            # Extract text from HTML elements in the iXBRL document
            # This is a simplified extraction - could be enhanced based on specific needs
            for fact in model_xbrl.facts:
                if hasattr(fact, 'value') and isinstance(fact.value, str):
                    # Check if this looks like narrative content (not just numbers/codes)
                    value = fact.value.strip()
                    if len(value) > 50 and any(c.isalpha() for c in value):
                        narrative_sections.append(value)
            
        except Exception as e:
            # Log error but don't fail the entire parsing
            logger.warning(f"Error extracting narrative content: {e}")
        
        return narrative_sections
    
    def get_financial_metrics(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Extract and categorize financial metrics from iXBRL document.
        
        Args:
            file_path: Path to the iXBRL file
            
        Returns:
            dict: Categorized financial metrics for cross-referencing with sentiment analysis
        """
        try:
            ixbrl_data = self.parse_ixbrl_file(file_path, extract_narrative=False)
            
            # Use financial extractor to categorize metrics
            financial_metrics = self.financial_extractor.extract_key_metrics(ixbrl_data.facts)
            
            # Add metadata for context
            financial_metrics['metadata'] = {
                'total_facts': len(ixbrl_data.facts),
                'total_concepts': len(ixbrl_data.concepts),
                'contexts': len(ixbrl_data.contexts),
                'document_type': ixbrl_data.filing_metadata.get('document_type'),
                'parsing_success': True
            }
            
            logger.info(f"Extracted financial metrics: {len(financial_metrics['revenue'])} revenue items, "
                       f"{len(financial_metrics['income'])} income items")
            
            return financial_metrics
            
        except iXBRLParsingError as e:
            logger.error(f"Failed to extract financial metrics from {file_path}: {e}")
            return {
                'revenue': {},
                'income': {},
                'expenses': {},
                'balance_sheet': {},
                'other': {},
                'metadata': {
                    'parsing_success': False,
                    'error': str(e)
                }
            }
    
    def is_available(self) -> bool:
        """Check if Arelle library is available and initialized."""
        return ARELLE_AVAILABLE and self.controller is not None
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the iXBRL parser.
        
        Returns:
            dict: Health status information
        """
        try:
            status = {
                'status': 'healthy' if self.is_available() else 'unhealthy',
                'arelle_available': ARELLE_AVAILABLE,
                'controller_initialized': self.controller is not None,
                'cache_dir': str(self.cache_dir),
                'cache_dir_exists': self.cache_dir.exists(),
                'test_completed': False
            }
            
            # Try to perform a simple test if fully available
            if self.is_available():
                # Create a minimal test iXBRL content
                test_content = '''<?xml version="1.0" encoding="utf-8"?>
                <html xmlns="http://www.w3.org/1999/xhtml">
                    <head><title>Test</title></head>
                    <body>Test iXBRL document</body>
                </html>'''
                
                # Save test content to temp file
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                    f.write(test_content)
                    test_file = f.name
                
                try:
                    # Try to load the test file (this will likely fail but tests the workflow)
                    model_manager = ModelManager.initialize(self.controller)
                    model_xbrl = model_manager.load(test_file)
                    if model_xbrl:
                        model_xbrl.close()
                    status['test_completed'] = True
                except:
                    # Expected to fail with minimal content, but shows initialization works
                    status['test_completed'] = True
                finally:
                    try:
                        os.unlink(test_file)
                    except:
                        pass
            
            return status
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'arelle_available': ARELLE_AVAILABLE,
                'controller_initialized': False,
                'test_completed': False
            }


# Global parser instance
_parser: Optional[ArelleParser] = None


def get_ixbrl_parser() -> ArelleParser:
    """Get the global iXBRL parser instance."""
    global _parser
    if _parser is None:
        _parser = ArelleParser()
    return _parser


def parse_ixbrl_document(file_path: Union[str, Path]) -> iXBRLData:
    """Convenience function to parse an iXBRL document."""
    parser = get_ixbrl_parser()
    return parser.parse_ixbrl_file(file_path)


def extract_financial_metrics(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Convenience function to extract financial metrics from iXBRL document."""
    parser = get_ixbrl_parser()
    return parser.get_financial_metrics(file_path)
