"""
Base Spec Processor
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class SpecProcessor(ABC):
    """Abstract base class for OpenAPI spec processors"""
    
    @abstractmethod
    def supports_provider(self, provider: str) -> bool:
        """Check if this processor supports the provider"""
        pass
    
    @abstractmethod
    def process_spec(self, spec_dict: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process the OpenAPI specification"""
        pass
