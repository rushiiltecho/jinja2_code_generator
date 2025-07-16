"""
Refactored Dynamic API Toolset Generator - Core Module
======================================================

This module provides a scalable, decoupled architecture for generating
ADK-compatible toolsets from OpenAPI specifications.
"""

import json
import yaml
import os
import shutil
from typing import Any, Dict, List, Optional, Union, Protocol
from dataclasses import dataclass, field
from pathlib import Path
from abc import ABC, abstractmethod
import jinja2
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """Configuration for an API provider"""
    name: str
    provider: str  # e.g., 'google', 'atlassian', 'slack'
    base_url: str
    spec_url: str
    auth_type: str  # "oauth2", "bearer", "api_key"
    scopes: Dict[str, str] = field(default_factory=dict)
    auth_endpoints: Dict[str, str] = field(default_factory=dict)
    custom_headers: Dict[str, str] = field(default_factory=dict)
    server_url_template: Optional[str] = None
    env_vars: Dict[str, str] = field(default_factory=dict)
    custom_processors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, yaml_file: Path) -> 'APIConfig':
        """Load configuration from YAML file"""
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, yaml_file: Path) -> None:
        """Save configuration to YAML file"""
        with open(yaml_file, 'w') as f:
            yaml.dump(self.__dict__, f, default_flow_style=False)


class SpecProcessor(ABC):
    """Abstract base class for OpenAPI spec processors"""
    
    @abstractmethod
    def process_spec(self, spec_dict: dict, config: APIConfig) -> dict:
        """Process the OpenAPI specification"""
        pass

    @abstractmethod
    def supports_provider(self, provider: str) -> bool:
        """Check if this processor supports the given provider"""
        pass


class TemplateRenderer:
    """Handles Jinja2 template rendering with extensible filters and functions"""
    
    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_dir)),
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self._register_custom_filters()
    
    def _register_custom_filters(self):
        """Register custom Jinja2 filters"""
        self.env.filters['to_class_name'] = self._to_class_name
        self.env.filters['to_snake_case'] = self._to_snake_case
        self.env.filters['to_env_var'] = self._to_env_var
    
    @staticmethod
    def _to_class_name(value: str) -> str:
        """Convert string to PascalCase class name"""
        return ''.join(word.capitalize() for word in value.replace('-', '_').split('_'))
    
    @staticmethod
    def _to_snake_case(value: str) -> str:
        """Convert string to snake_case"""
        return value.replace('-', '_').lower()
    
    @staticmethod
    def _to_env_var(value: str) -> str:
        """Convert string to UPPER_CASE environment variable name"""
        return value.replace('-', '_').upper()
    
    def render_template(self, template_name: str, **context) -> str:
        """Render a template with the given context"""
        template = self.env.get_template(template_name)
        return template.render(**context)


class ConfigManager:
    """Manages API configurations and provider-specific settings"""
    
    def __init__(self, config_root: Path):
        self.config_root = config_root
        self.providers_dir = config_root / "providers"
        self.templates_dir = config_root / "templates"
        self.ensure_structure()
    
    def ensure_structure(self):
        """Ensure the configuration directory structure exists"""
        directories = [
            self.config_root,
            self.providers_dir,
            self.templates_dir,
            self.templates_dir / "toolsets",
            self.templates_dir / "auth",
            self.templates_dir / "processors"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def load_provider_configs(self, provider: str) -> List[APIConfig]:
        """Load all configurations for a specific provider"""
        provider_dir = self.providers_dir / provider
        if not provider_dir.exists():
            return []
        
        configs = []
        for config_file in provider_dir.glob("*.yaml"):
            try:
                config = APIConfig.from_yaml(config_file)
                config.provider = provider  # Ensure provider is set
                configs.append(config)
            except Exception as e:
                logger.error(f"Failed to load config {config_file}: {e}")
        
        return configs
    
    def load_all_configs(self) -> Dict[str, List[APIConfig]]:
        """Load all configurations grouped by provider"""
        all_configs = {}
        
        for provider_dir in self.providers_dir.iterdir():
            if provider_dir.is_dir():
                provider = provider_dir.name
                configs = self.load_provider_configs(provider)
                if configs:
                    all_configs[provider] = configs
        
        return all_configs
    
    def save_config(self, config: APIConfig, api_name: str):
        """Save a configuration to the appropriate provider directory"""
        provider_dir = self.providers_dir / config.provider
        provider_dir.mkdir(exist_ok=True)
        
        config_file = provider_dir / f"{api_name}.yaml"
        config.to_yaml(config_file)


class SpecProcessorRegistry:
    """Registry for OpenAPI spec processors"""
    
    def __init__(self):
        self._processors: List[SpecProcessor] = []
    
    def register(self, processor: SpecProcessor):
        """Register a spec processor"""
        self._processors.append(processor)
    
    def get_processor(self, provider: str) -> Optional[SpecProcessor]:
        """Get the appropriate processor for a provider"""
        for processor in self._processors:
            if processor.supports_provider(provider):
                return processor
        return None
    
    def list_supported_providers(self) -> List[str]:
        """List all supported providers"""
        providers = set()
        for processor in self._processors:
            # This would need to be implemented based on processor capabilities
            pass
        return list(providers)


class ToolsetGenerator:
    """Core toolset generator with pluggable architecture"""
    
    def __init__(self, config_root: Path):
        self.config_manager = ConfigManager(config_root)
        self.template_renderer = TemplateRenderer(self.config_manager.templates_dir)
        self.spec_registry = SpecProcessorRegistry()
        self._initialize_default_processors()
    
    def _initialize_default_processors(self):
        """Initialize default spec processors"""
        # Import and register default processors
        from .processors import AtlassianSpecProcessor
        from .processors import GoogleSpecProcessor
        from .processors import SlackSpecProcessor
        from .processors import SalesforceSpecProcessor
        from .processors import GenericSpecProcessor
        
        self.spec_registry.register(AtlassianSpecProcessor())
        self.spec_registry.register(GoogleSpecProcessor())
        self.spec_registry.register(SlackSpecProcessor())
        self.spec_registry.register(SalesforceSpecProcessor())
        self.spec_registry.register(GenericSpecProcessor())  # Fallback
    
    def generate_toolset(self, provider: str, api_name: str, output_dir: Path) -> Path:
        """Generate a toolset for a specific API"""
        # Load configuration
        configs = self.config_manager.load_provider_configs(provider)
        config = next((c for c in configs if c.name.lower().replace(' ', '_') == api_name), None)
        
        if not config:
            raise ValueError(f"Configuration not found for {provider}/{api_name}")
        
        # Get appropriate processor
        processor = self.spec_registry.get_processor(provider)
        if not processor:
            logger.warning(f"No specific processor for {provider}, using generic processor")
            processor = self.spec_registry.get_processor("generic")
        
        # Prepare template context
        context = self._prepare_template_context(config, processor)
        
        # Render toolset
        output_dir.mkdir(parents=True, exist_ok=True)
        toolset_file = output_dir / f"{api_name}_toolset.py"
        
        rendered_code = self.template_renderer.render_template(
            "toolsets/base_toolset.py.j2", 
            **context
        )
        
        with open(toolset_file, 'w') as f:
            f.write(rendered_code)
        
        logger.info(f"Generated toolset: {toolset_file}")
        return toolset_file
    
    def generate_provider_toolsets(self, provider: str, output_dir: Path) -> List[Path]:
        """Generate all toolsets for a provider"""
        configs = self.config_manager.load_provider_configs(provider)
        generated_files = []
        
        for config in configs:
            try:
                api_name = config.name.lower().replace(' ', '_').replace('-', '_')
                file_path = self.generate_toolset(provider, api_name, output_dir)
                generated_files.append(file_path)
            except Exception as e:
                logger.error(f"Failed to generate toolset for {config.name}: {e}")
        
        return generated_files
    
    def generate_all_toolsets(self, output_dir: Path) -> Dict[str, List[Path]]:
        """Generate toolsets for all providers"""
        all_configs = self.config_manager.load_all_configs()
        results = {}
        
        for provider, configs in all_configs.items():
            generated_files = self.generate_provider_toolsets(provider, output_dir)
            results[provider] = generated_files
        
        # Generate unified registry
        self._generate_registry(output_dir, results)
        
        return results
    
    def _prepare_template_context(self, config: APIConfig, processor: Optional[SpecProcessor]) -> Dict[str, Any]:
        """Prepare the template rendering context"""
        api_name = config.name.lower().replace(' ', '_').replace('-', '_')
        class_name = self.template_renderer._to_class_name(api_name)
        
        # Convert APIConfig to a dictionary for template serialization
        config_dict = {
            'name': config.name,
            'provider': config.provider,
            'base_url': config.base_url,
            'spec_url': config.spec_url,
            'auth_type': config.auth_type,
            'scopes': config.scopes,
            'auth_endpoints': config.auth_endpoints,
            'custom_headers': config.custom_headers,
            'server_url_template': config.server_url_template,
            'env_vars': config.env_vars,
            'custom_processors': getattr(config, 'custom_processors', []),
            'metadata': config.metadata
        }
        
        context = {
            'config': config_dict,
            'api_name': api_name,
            'class_name': class_name,
            'provider': config.provider,
            'has_processor': processor is not None,
            'processor_name': processor.__class__.__name__ if processor else None
        }
        
        return context
    
    def _generate_registry(self, output_dir: Path, results: Dict[str, List[Path]]):
        """Generate a unified registry for all toolsets"""
        registry_context = {
            'providers': results,
            'all_toolsets': []
        }
        
        # Collect all toolset information
        for provider, files in results.items():
            for file_path in files:
                api_name = file_path.stem.replace('_toolset', '')
                class_name = self.template_renderer._to_class_name(api_name)
                registry_context['all_toolsets'].append({
                    'provider': provider,
                    'api_name': api_name,
                    'class_name': class_name,
                    'module_name': file_path.stem
                })
        
        # Render registry
        registry_content = self.template_renderer.render_template(
            "registry/__init__.py.j2",
            **registry_context
        )
        
        registry_file = output_dir / "__init__.py"
        with open(registry_file, 'w') as f:
            f.write(registry_content)
        
        logger.info(f"Generated registry: {registry_file}")


class CLIInterface:
    """Command-line interface for the toolset generator"""
    
    def __init__(self, config_root: Path = Path("toolset_configs")):
        self.generator = ToolsetGenerator(config_root)
    
    def init_project(self, force: bool = False):
        """Initialize a new project with default configurations"""
        if self.generator.config_manager.config_root.exists() and not force:
            print(f"Configuration directory already exists: {self.generator.config_manager.config_root}")
            print("Use --force to overwrite")
            return
        
        # Create default structure and templates
        self._create_default_templates()
        self._create_default_configs()
        print(f"Initialized project in {self.generator.config_manager.config_root}")
    
    def list_providers(self):
        """List all available providers"""
        all_configs = self.generator.config_manager.load_all_configs()
        print("Available providers:")
        for provider, configs in all_configs.items():
            print(f"  {provider}: {len(configs)} APIs")
            for config in configs:
                api_name = config.name.lower().replace(' ', '_')
                print(f"    - {api_name}")
    
    def generate(self, provider: str = None, api: str = None, output_dir: str = "generated_toolsets"):
        """Generate toolsets"""
        output_path = Path(output_dir)
        
        if provider and api:
            # Generate specific API
            file_path = self.generator.generate_toolset(provider, api, output_path)
            print(f"Generated: {file_path}")
        elif provider:
            # Generate all APIs for provider
            files = self.generator.generate_provider_toolsets(provider, output_path)
            print(f"Generated {len(files)} toolsets for {provider}")
        else:
            # Generate all
            results = self.generator.generate_all_toolsets(output_path)
            total = sum(len(files) for files in results.values())
            print(f"Generated {total} toolsets across {len(results)} providers")
    
    def _create_default_templates(self):
        """Create default Jinja2 templates"""
        templates_dir = self.generator.config_manager.templates_dir
        
        # We'll create these template files separately
        template_files = {
            "toolsets/base_toolset.py.j2": "base_toolset_template.j2",
            "auth/oauth2.py.j2": "oauth2_auth_template.j2", 
            "auth/bearer.py.j2": "bearer_auth_template.j2",
            "registry/__init__.py.j2": "registry_template.j2"
        }
        
        for template_path, source_file in template_files.items():
            template_file = templates_dir / template_path
            template_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create placeholder templates (these would be separate files)
            if not template_file.exists():
                with open(template_file, 'w') as f:
                    f.write(f"# Template: {template_path}\n# TODO: Implement template content\n")
    
    def _create_default_configs(self):
        """Create default provider configurations"""
        # This will trigger the creation of default provider configs
        providers = ['google', 'atlassian', 'slack', 'salesforce']
        
        for provider in providers:
            provider_dir = self.generator.config_manager.providers_dir / provider
            provider_dir.mkdir(exist_ok=True)
            
            # Create a placeholder config if none exists
            if not list(provider_dir.glob("*.yaml")):
                placeholder_file = provider_dir / "example.yaml"
                with open(placeholder_file, 'w') as f:
                    f.write(f"# Example configuration for {provider} provider\n")
                    f.write("# Copy and modify this file for your APIs\n")


def main():
    """Main entry point for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dynamic API Toolset Generator")
    parser.add_argument("--config-dir", default="toolset_configs", 
                       help="Configuration directory")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize new project")
    init_parser.add_argument("--force", action="store_true", 
                            help="Overwrite existing configuration")
    
    # List command
    subparsers.add_parser("list", help="List available providers and APIs")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate toolsets")
    gen_parser.add_argument("--provider", help="Specific provider to generate")
    gen_parser.add_argument("--api", help="Specific API to generate")
    gen_parser.add_argument("--output", default="generated_toolsets", 
                           help="Output directory")
    
    args = parser.parse_args()
    
    cli = CLIInterface(Path(args.config_dir))
    
    if args.command == "init":
        cli.init_project(args.force)
    elif args.command == "list":
        cli.list_providers()
    elif args.command == "generate":
        cli.generate(args.provider, args.api, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()