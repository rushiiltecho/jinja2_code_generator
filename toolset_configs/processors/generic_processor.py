"""
Generic API Spec Processor
"""

from typing import Dict, Any
from .base_processor import SpecProcessor


class GenericSpecProcessor(SpecProcessor):
    """Processor for Generic APIs"""
    
    def supports_provider(self, provider: str) -> bool:
        return provider.lower() == "generic"
    
    def process_spec(self, spec_dict: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process Generic OpenAPI specification"""
        # Add Generic-specific processing here
        return spec_dict
