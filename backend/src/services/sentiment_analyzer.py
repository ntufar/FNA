"""
SentimentAnalyzer service for FNA Platform.

Implements multi-dimensional sentiment analysis using Qwen3-4B model via LM Studio API
for financial narrative text processing.
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..core.config import get_settings
from ..core.exceptions import ModelInferenceError, log_performance
from ..models import NarrativeAnalysis

logger = logging.getLogger(__name__)


class SentimentAnalysisResult:
    """Container for sentiment analysis results."""
    
    def __init__(
        self,
        optimism_score: float,
        optimism_confidence: float,
        risk_score: float,
        risk_confidence: float,
        uncertainty_score: float,
        uncertainty_confidence: float,
        key_themes: List[str],
        risk_indicators: List[str],
        narrative_sections: Dict[str, str],
        processing_time_seconds: int,
        model_version: str
    ):
        self.optimism_score = optimism_score
        self.optimism_confidence = optimism_confidence
        self.risk_score = risk_score
        self.risk_confidence = risk_confidence
        self.uncertainty_score = uncertainty_score
        self.uncertainty_confidence = uncertainty_confidence
        self.key_themes = key_themes
        self.risk_indicators = risk_indicators
        self.narrative_sections = narrative_sections
        self.processing_time_seconds = processing_time_seconds
        self.model_version = model_version
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            'optimism_score': self.optimism_score,
            'optimism_confidence': self.optimism_confidence,
            'risk_score': self.risk_score,
            'risk_confidence': self.risk_confidence,
            'uncertainty_score': self.uncertainty_score,
            'uncertainty_confidence': self.uncertainty_confidence,
            'key_themes': self.key_themes,
            'risk_indicators': self.risk_indicators,
            'narrative_sections': self.narrative_sections,
            'processing_time_seconds': self.processing_time_seconds,
            'model_version': self.model_version
        }
    
    def validate_scores(self) -> bool:
        """Validate all scores are within valid range (0.0-1.0)."""
        scores = [
            self.optimism_score, self.optimism_confidence,
            self.risk_score, self.risk_confidence,
            self.uncertainty_score, self.uncertainty_confidence
        ]
        return all(0.0 <= score <= 1.0 for score in scores)


class SentimentAnalyzer:
    """
    Sentiment analyzer using Qwen3-4B model via LM Studio API.
    
    Performs multi-dimensional sentiment analysis on financial narratives,
    extracting optimism, risk, and uncertainty scores with confidence metrics.
    """
    
    def __init__(self):
        """Initialize the sentiment analyzer with LM Studio configuration."""
        self.settings = get_settings()
        self.model_name = self.settings.model_name
        self.api_url = self.settings.model_api_url.rstrip('/')
        self.api_timeout = self.settings.model_api_timeout
        self.max_tokens = self.settings.model_max_tokens
        self.temperature = self.settings.model_temperature
        self.top_p = self.settings.model_top_p
        
        # Setup HTTP session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        logger.info(f"SentimentAnalyzer initialized with {self.model_name} at {self.api_url}")
    
    def _build_analysis_prompt(self, text: str, section_type: str = "financial_report") -> str:
        """
        Build a comprehensive prompt for multi-dimensional sentiment analysis.
        
        Args:
            text: Text to analyze
            section_type: Type of document section being analyzed
            
        Returns:
            str: Formatted prompt for the model
        """
        prompt = f"""You are a financial narrative analyzer. Analyze the following {section_type} text and provide multi-dimensional sentiment scores.

IMPORTANT: Respond ONLY with a valid JSON object containing the requested fields. Do not include any additional text, explanations, or formatting.

TEXT TO ANALYZE:
{text}

Required JSON Response Format:
{{
    "optimism_score": <float 0.0-1.0>,
    "optimism_confidence": <float 0.0-1.0>,
    "risk_score": <float 0.0-1.0>,
    "risk_confidence": <float 0.0-1.0>,
    "uncertainty_score": <float 0.0-1.0>,
    "uncertainty_confidence": <float 0.0-1.0>,
    "key_themes": [<list of 3-10 main themes as strings>],
    "risk_indicators": [<list of risk-related phrases/words found>],
    "narrative_sections": {{
        "summary": "<brief 1-2 sentence summary>",
        "tone": "<overall tone description>",
        "outlook": "<forward-looking sentiment>"
    }}
}}

Scoring Guidelines:
- optimism_score: 0.0=very pessimistic, 0.5=neutral, 1.0=very optimistic
- risk_score: 0.0=low risk perception, 0.5=moderate, 1.0=high risk perception  
- uncertainty_score: 0.0=very certain/clear, 0.5=some uncertainty, 1.0=very uncertain
- confidence: 0.0=low confidence in score, 1.0=high confidence in score
- key_themes: Extract 3-10 main narrative themes (e.g., "market expansion", "cost management")
- risk_indicators: Identify specific risk-related language (e.g., "challenging", "uncertain", "headwinds")

Focus on financial context, management tone, forward guidance, and strategic positioning."""

        return prompt
    
    def _call_llm_api(self, prompt: str) -> Dict[str, Any]:
        """
        Make API call to LM Studio for text generation.
        
        Args:
            prompt: Formatted prompt for analysis
            
        Returns:
            dict: API response data
            
        Raises:
            ModelInferenceError: If API call fails
        """
        try:
            # Prepare API request
            api_endpoint = f"{self.api_url}/v1/chat/completions"
            
            headers = {
                'Content-Type': 'application/json',
            }
            
            payload = {
                'model': self.model_name,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': self.temperature,
                'top_p': self.top_p,
                'max_tokens': self.max_tokens,
                'stream': False
            }
            
            logger.debug(f"Making LM Studio API call to {api_endpoint}")
            
            # Make API request
            response = self.session.post(
                api_endpoint,
                headers=headers,
                json=payload,
                timeout=self.api_timeout
            )
            
            response.raise_for_status()
            
            response_data = response.json()
            
            # Extract generated text from response
            if 'choices' not in response_data or not response_data['choices']:
                raise ModelInferenceError("No choices in LM Studio response")
            
            generated_text = response_data['choices'][0]['message']['content'].strip()
            
            logger.debug(f"LM Studio API call successful, generated {len(generated_text)} characters")
            
            return {
                'generated_text': generated_text,
                'usage': response_data.get('usage', {}),
                'model': response_data.get('model', self.model_name)
            }
            
        except requests.exceptions.Timeout:
            raise ModelInferenceError(f"LM Studio API timeout after {self.api_timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise ModelInferenceError(f"Cannot connect to LM Studio at {self.api_url}")
        except requests.exceptions.RequestException as e:
            raise ModelInferenceError(f"LM Studio API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise ModelInferenceError(f"Invalid JSON response from LM Studio: {str(e)}")
    
    def _parse_llm_response(self, generated_text: str) -> Dict[str, Any]:
        """
        Parse and validate LLM response JSON.
        
        Args:
            generated_text: Generated text from LLM
            
        Returns:
            dict: Parsed and validated sentiment data
            
        Raises:
            ModelInferenceError: If parsing or validation fails
        """
        try:
            # Try to extract JSON from response (model might add extra text)
            text = generated_text.strip()
            
            # Find JSON object boundaries
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            
            if start_idx == -1 or end_idx == -1 or start_idx >= end_idx:
                raise ValueError("No valid JSON object found in response")
            
            json_text = text[start_idx:end_idx + 1]
            
            # Parse JSON
            parsed_data = json.loads(json_text)
            
            # Validate required fields
            required_fields = [
                'optimism_score', 'optimism_confidence',
                'risk_score', 'risk_confidence', 
                'uncertainty_score', 'uncertainty_confidence',
                'key_themes', 'risk_indicators', 'narrative_sections'
            ]
            
            for field in required_fields:
                if field not in parsed_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate score ranges
            score_fields = [
                'optimism_score', 'optimism_confidence',
                'risk_score', 'risk_confidence',
                'uncertainty_score', 'uncertainty_confidence'
            ]
            
            for field in score_fields:
                score = parsed_data[field]
                if not isinstance(score, (int, float)) or not (0.0 <= score <= 1.0):
                    raise ValueError(f"Invalid score for {field}: {score} (must be 0.0-1.0)")
            
            # Validate arrays
            if not isinstance(parsed_data['key_themes'], list):
                raise ValueError("key_themes must be a list")
            
            if not isinstance(parsed_data['risk_indicators'], list):
                raise ValueError("risk_indicators must be a list")
            
            if not isinstance(parsed_data['narrative_sections'], dict):
                raise ValueError("narrative_sections must be a dictionary")
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            raise ModelInferenceError(f"Failed to parse LLM response as JSON: {str(e)}")
        except ValueError as e:
            raise ModelInferenceError(f"Invalid LLM response format: {str(e)}")
    
    @log_performance("sentiment_analysis")
    def analyze_text(
        self,
        text: str,
        section_type: str = "financial_report",
        max_length: int = 8000
    ) -> SentimentAnalysisResult:
        """
        Perform multi-dimensional sentiment analysis on text.
        
        Args:
            text: Text content to analyze
            section_type: Type of document section
            max_length: Maximum text length to process
            
        Returns:
            SentimentAnalysisResult: Complete analysis results
            
        Raises:
            ModelInferenceError: If analysis fails
        """
        logger.info(f"=====================================================")
        logger.info(f"Analyzing text length: {len(text)}")
        #logger.info(f"Analyzing text: {text}")
        start_time = time.time()
        
        try:
            # Truncate text if too long
            if len(text) > max_length:
                text = text[:max_length] + "..."
                logger.warning(f"Text truncated to {max_length} characters")
            
            # Build prompt
            prompt = self._build_analysis_prompt(text, section_type)
            
            # Call LLM API
            logger.info("Starting sentiment analysis with Qwen3-4B")
            api_response = self._call_llm_api(prompt)
            
            # Parse response
            sentiment_data = self._parse_llm_response(api_response['generated_text'])
            
            # Calculate processing time
            processing_time = int(time.time() - start_time)
            
            # Create result object
            result = SentimentAnalysisResult(
                optimism_score=sentiment_data['optimism_score'],
                optimism_confidence=sentiment_data['optimism_confidence'],
                risk_score=sentiment_data['risk_score'],
                risk_confidence=sentiment_data['risk_confidence'],
                uncertainty_score=sentiment_data['uncertainty_score'],
                uncertainty_confidence=sentiment_data['uncertainty_confidence'],
                key_themes=sentiment_data['key_themes'],
                risk_indicators=sentiment_data['risk_indicators'],
                narrative_sections=sentiment_data['narrative_sections'],
                processing_time_seconds=processing_time,
                model_version=api_response.get('model', self.model_name)
            )
            
            # Validate result
            if not result.validate_scores():
                raise ModelInferenceError("Generated sentiment scores are out of valid range")
            
            # Check performance requirement (<60 seconds)
            if processing_time > 60:
                logger.warning(f"Analysis took {processing_time}s, exceeding 60s requirement")
            
            logger.info(
                f"Sentiment analysis completed in {processing_time}s: "
                f"optimism={result.optimism_score:.2f}, "
                f"risk={result.risk_score:.2f}, "
                f"uncertainty={result.uncertainty_score:.2f}"
            )
            
            return result
            
        except Exception as e:
            processing_time = int(time.time() - start_time)
            logger.error(f"Sentiment analysis failed after {processing_time}s: {str(e)}")
            raise ModelInferenceError(f"Sentiment analysis failed: {str(e)}")
    
    def analyze_document_sections(
        self,
        sections: Dict[str, str]
    ) -> Dict[str, SentimentAnalysisResult]:
        """
        Analyze multiple document sections and return combined results.
        
        Args:
            sections: Dictionary mapping section names to text content
            
        Returns:
            dict: Results for each section
        """
        results = {}
        
        for section_name, text_content in sections.items():
            if text_content and text_content.strip():
                try:
                    logger.info(f"Analyzing section: {section_name}")
                    result = self.analyze_text(text_content, section_name)
                    results[section_name] = result
                except ModelInferenceError as e:
                    logger.error(f"Failed to analyze section {section_name}: {e}")
                    results[section_name] = None
            else:
                logger.warning(f"Skipping empty section: {section_name}")
                results[section_name] = None
        
        return results
    
    def create_analysis_record(
        self,
        result: SentimentAnalysisResult,
        report_id: str,
        financial_metrics: Optional[Dict[str, Any]] = None
    ) -> NarrativeAnalysis:
        """
        Create a NarrativeAnalysis model instance from analysis results.
        
        Args:
            result: Sentiment analysis results
            report_id: UUID of the financial report
            financial_metrics: Optional iXBRL financial data
            
        Returns:
            NarrativeAnalysis: Model instance ready for database storage
        """
        return NarrativeAnalysis(
            report_id=report_id,
            optimism_score=result.optimism_score,
            optimism_confidence=result.optimism_confidence,
            risk_score=result.risk_score,
            risk_confidence=result.risk_confidence,
            uncertainty_score=result.uncertainty_score,
            uncertainty_confidence=result.uncertainty_confidence,
            key_themes=result.key_themes,
            risk_indicators=result.risk_indicators,
            narrative_sections=result.narrative_sections,
            financial_metrics=financial_metrics,
            processing_time_seconds=result.processing_time_seconds,
            model_version=result.model_version
        )
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the LM Studio connection and model.
        
        Returns:
            dict: Health status information
        """
        try:
            # Test with simple prompt
            test_prompt = self._build_analysis_prompt(
                "The company reported strong quarterly results with increased revenue.",
                "test_section"
            )
            
            start_time = time.time()
            api_response = self._call_llm_api(test_prompt)
            response_time = time.time() - start_time
            
            # Parse response to verify format
            sentiment_data = self._parse_llm_response(api_response['generated_text'])
            
            return {
                'status': 'healthy',
                'model_name': api_response.get('model', self.model_name),
                'api_url': self.api_url,
                'response_time_seconds': round(response_time, 2),
                'test_completed': True
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'model_name': self.model_name,
                'api_url': self.api_url,
                'error': str(e),
                'test_completed': False
            }
