"""
Atlassian API Spec Processor
"""

from typing import Dict, Any
from .base_processor import SpecProcessor


class AtlassianSpecProcessor(SpecProcessor):
    """Processor for Atlassian APIs"""
    
    def supports_provider(self, provider: str) -> bool:
        return provider.lower() == "atlassian"
    
    def process_spec(self, spec_dict: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process Atlassian OpenAPI specification"""
        # Add Atlassian-specific processing here
        return spec_dict
