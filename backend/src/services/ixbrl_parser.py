"""iXBRL Parser Service using Arelle library.

This module handles parsing of iXBRL (Inline eXtensible Business Reporting Language)
documents as specified in research.md.
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from pydantic import BaseSettings

# Arelle imports - these will be available after pip install arelle
try:
    from arelle import Cntlr, ModelManager, PackageManager
    from arelle.ModelDocument import ModelDocument
    from arelle.ModelXbrl import ModelXbrl
    ARELLE_AVAILABLE = True
except ImportError:
    ARELLE_AVAILABLE = False


class ArelleSettings(BaseSettings):
    """Arelle configuration settings from environment variables."""
    
    log_level: str = "WARNING"
    cache_dir: str = "./arelle_cache"
    
    class Config:
        env_prefix = "ARELLE_"


@dataclass
class iXBRLData:
    """Structured data extracted from iXBRL document."""
    
    facts: Dict[str, Any]
    concepts: List[str]
    contexts: Dict[str, Any]
    units: Dict[str, Any]
    narrative_sections: List[str]
    filing_metadata: Dict[str, Any]


class iXBRLParsingError(Exception):
    """Exception raised when iXBRL parsing fails."""
    pass


class ArelleParser:
    """Arelle-based iXBRL parser for SEC financial filings."""
    
    def __init__(self, settings: Optional[ArelleSettings] = None):
        self.settings = settings or ArelleSettings()
        self.controller: Optional[Cntlr.Cntlr] = None
        self._initialize_arelle()
    
    def _initialize_arelle(self) -> None:
        """Initialize Arelle controller and configuration."""
        if not ARELLE_AVAILABLE:
            raise ImportError(
                "Arelle library not available. Install with: pip install arelle"
            )
        
        try:
            # Create cache directory
            cache_path = Path(self.settings.cache_dir)
            cache_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize Arelle controller
            self.controller = Cntlr.Cntlr(logFileName=None)
            self.controller.webCache.workOffline = False
            
            # Set log level
            log_levels = {
                "DEBUG": 10,
                "INFO": 20, 
                "WARNING": 30,
                "ERROR": 40,
                "CRITICAL": 50
            }
            level = log_levels.get(self.settings.log_level.upper(), 30)
            self.controller.logger.setLevel(level)
            
        except Exception as e:
            raise iXBRLParsingError(f"Failed to initialize Arelle: {e}")
    
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
            raise iXBRLParsingError(f"File not found: {file_path}")
        
        try:
            # Load the iXBRL document
            model_manager = ModelManager.initialize(self.controller)
            model_xbrl = model_manager.load(str(file_path))
            
            if model_xbrl is None:
                raise iXBRLParsingError("Failed to load iXBRL document")
            
            # Extract structured data
            facts = self._extract_facts(model_xbrl)
            concepts = self._extract_concepts(model_xbrl)
            contexts = self._extract_contexts(model_xbrl)
            units = self._extract_units(model_xbrl)
            metadata = self._extract_metadata(model_xbrl)
            
            # Extract narrative content if requested
            narrative_sections = []
            if extract_narrative:
                narrative_sections = self._extract_narrative_content(model_xbrl)
            
            return iXBRLData(
                facts=facts,
                concepts=concepts,
                contexts=contexts,
                units=units,
                narrative_sections=narrative_sections,
                filing_metadata=metadata
            )
            
        except Exception as e:
            raise iXBRLParsingError(f"Error parsing iXBRL file: {e}")
        
        finally:
            # Clean up resources
            if model_xbrl:
                model_xbrl.close()
    
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
            print(f"Warning: Error extracting narrative content: {e}")
        
        return narrative_sections
    
    def is_available(self) -> bool:
        """Check if Arelle library is available and initialized."""
        return ARELLE_AVAILABLE and self.controller is not None


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
