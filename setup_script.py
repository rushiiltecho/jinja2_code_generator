#!/usr/bin/env python3
"""
Dynamic API Toolset Generator - Setup and Installation Script
=============================================================

This script sets up the complete refactored Dynamic API Toolset Generator
with all necessary components, templates, and configurations.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import yaml
import json


class SetupManager:
    """Manages the setup and installation of the Dynamic API Toolset Generator"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.toolset_configs_dir = self.project_root / "toolset_configs"
        self.generated_dir = self.project_root / "generated_toolsets"
        
    def run_complete_setup(self):
        """Run the complete setup process"""
        print("🚀 Setting up Dynamic API Toolset Generator")
        print("=" * 50)
        
        steps = [
            ("Creating directory structure", self.create_directory_structure),
            ("Installing dependencies", self.install_dependencies),
            ("Creating configuration files", self.create_configurations),
            ("Creating template files", self.create_templates),
            ("Creating processor modules", self.create_processors),
            ("Setting up CLI tool", self.setup_cli),
            ("Creating example files", self.create_examples),
            ("Running initial generation", self.initial_generation),
            ("Creating documentation", self.create_documentation)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            try:
                step_func()
                print(f"✅ {step_name} completed")
            except Exception as e:
                print(f"❌ {step_name} failed: {e}")
                raise
        
        print(f"\n🎉 Setup completed successfully!")
        print(f"📁 Project root: {self.project_root}")
        self.print_next_steps()
    
    def create_directory_structure(self):
        """Create the necessary directory structure"""
        directories = [
            self.toolset_configs_dir,
            self.toolset_configs_dir / "providers" / "google",
            self.toolset_configs_dir / "providers" / "atlassian", 
            self.toolset_configs_dir / "providers" / "slack",
            self.toolset_configs_dir / "providers" / "salesforce",
            self.toolset_configs_dir / "providers" / "microsoft",
            self.toolset_configs_dir / "providers" / "hubspot",
            self.toolset_configs_dir / "providers" / "github",
            self.toolset_configs_dir / "templates" / "toolsets",
            self.toolset_configs_dir / "templates" / "auth",
            self.toolset_configs_dir / "templates" / "registry",
            self.toolset_configs_dir / "templates" / "cli",
            self.toolset_configs_dir / "processors",
            self.generated_dir,
            self.project_root / "examples",
            self.project_root / "docs",
            self.project_root / "scripts"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def install_dependencies(self):
        """Install required Python dependencies"""
        requirements = [
            "google-adk>=0.1.0",
            "jinja2>=3.1.0", 
            "pyyaml>=6.0",
            "requests>=2.28.0",
            "python-dotenv>=1.0.0",
            "click>=8.0.0",
            "rich>=13.0.0",  # For better CLI output
            "typer>=0.9.0"   # Alternative CLI framework
        ]
        
        # Create requirements.txt
        requirements_file = self.project_root / "requirements.txt"
        with open(requirements_file, 'w') as f:
            f.write('\n'.join(requirements))
        
        print(f"  📄 Created {requirements_file}")
        
        # Try to install dependencies
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], check=True, capture_output=True)
            print("  📦 Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  Could not install dependencies automatically: {e}")
            print(f"  💡 Please run: pip install -r {requirements_file}")
    
    def create_configurations(self):
        """Create provider configuration files"""
        configs = {
            "google/calendar.yaml": {
                "name": "Google Calendar API",
                "provider": "google",
                "base_url": "https://www.googleapis.com/calendar/v3",
                "spec_url": "https://www.googleapis.com/discovery/v1/apis/calendar/v3/rest",
                "auth_type": "oauth2",
                "scopes": {
                    "readonly": "https://www.googleapis.com/auth/calendar.readonly",
                    "events": "https://www.googleapis.com/auth/calendar.events",
                    "full": "https://www.googleapis.com/auth/calendar"
                },
                "auth_endpoints": {
                    "authorization_url": "https://accounts.google.com/o/oauth2/auth",
                    "token_url": "https://oauth2.googleapis.com/token",
                    "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                    "revocation_url": "https://oauth2.googleapis.com/revoke"
                },
                "env_vars": {
                    "client_id": "GOOGLE_CLIENT_ID",
                    "client_secret": "GOOGLE_CLIENT_SECRET"
                },
                "metadata": {
                    "documentation": "https://developers.google.com/calendar/api"
                }
            },
            "google/drive.yaml": {
                "name": "Google Drive API",
                "provider": "google",
                "base_url": "https://www.googleapis.com/drive/v3",
                "spec_url": "https://www.googleapis.com/discovery/v1/apis/drive/v3/rest",
                "auth_type": "oauth2",
                "scopes": {
                    "readonly": "https://www.googleapis.com/auth/drive.readonly",
                    "file": "https://www.googleapis.com/auth/drive.file",
                    "full": "https://www.googleapis.com/auth/drive"
                },
                "auth_endpoints": {
                    "authorization_url": "https://accounts.google.com/o/oauth2/auth",
                    "token_url": "https://oauth2.googleapis.com/token"
                },
                "env_vars": {
                    "client_id": "GOOGLE_CLIENT_ID",
                    "client_secret": "GOOGLE_CLIENT_SECRET"
                },
                "metadata": {
                    "documentation": "https://developers.google.com/drive/api"
                }
            },
            "slack/web_api.yaml": {
                "name": "Slack Web API",
                "provider": "slack",
                "base_url": "https://slack.com/api",
                "spec_url": "https://raw.githubusercontent.com/slackapi/slack-api-specs/master/web-api/slack_web_openapi_v2.json",
                "auth_type": "bearer",
                "scopes": {
                    "channels_read": "channels:read",
                    "chat_write": "chat:write",
                    "users_read": "users:read"
                },
                "env_vars": {
                    "access_token": "SLACK_BOT_TOKEN"
                },
                "metadata": {
                    "documentation": "https://api.slack.com/web"
                }
            },
            "atlassian/jira.yaml": {
                "name": "Atlassian Jira Cloud API",
                "provider": "atlassian",
                "base_url": "https://api.atlassian.com/ex/jira/{cloud_id}",
                "spec_url": "https://developer.atlassian.com/cloud/jira/platform/swagger-v3.v3.json",
                "auth_type": "oauth2",
                "server_url_template": "https://api.atlassian.com/ex/jira/{{ cloud_id }}",
                "scopes": {
                    "read_work": "read:jira-work",
                    "write_work": "write:jira-work"
                },
                "auth_endpoints": {
                    "authorization_url": "https://auth.atlassian.com/authorize",
                    "token_url": "https://auth.atlassian.com/oauth/token"
                },
                "env_vars": {
                    "client_id": "JIRA_CLIENT_ID",
                    "client_secret": "JIRA_CLIENT_SECRET",
                    "cloud_id": "JIRA_CLOUD_ID"
                },
                "metadata": {
                    "documentation": "https://developer.atlassian.com/cloud/jira/platform/rest/"
                }
            }
        }
        
        for config_path, config_data in configs.items():
            file_path = self.toolset_configs_dir / "providers" / config_path
            with open(file_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
            print(f"  📄 Created {file_path}")
    
    def create_templates(self):
        """Create Jinja2 template files"""
        # Base toolset template (simplified version)
        base_toolset_template = '''"""
{{ config.name }} Toolset - Generated for Google ADK
Provider: {{ config.provider }}
Auth: {{ config.auth_type }}
"""

import json
import os
import requests
from typing import Any, List, Optional, Union, Dict

from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.openapi_tool import OpenAPIToolset
from google.adk.auth.auth_credential import AuthCredential, AuthCredentialTypes, HttpAuth, HttpCredentials


class {{ class_name }}(BaseToolset):
    """{{ config.name }} toolset for Google ADK"""
    
    def __init__(self, **kwargs):
        # Configuration from template
        self.config = {{ config | tojson }}
        
        # Authentication setup
        {% if config.auth_type == "bearer" -%}
        self.access_token = kwargs.get('access_token') or os.getenv('{{ config.env_vars.get("access_token", "ACCESS_TOKEN") }}')
        {% elif config.auth_type == "oauth2" -%}
        self.client_id = kwargs.get('client_id') or os.getenv('{{ config.env_vars.get("client_id", "CLIENT_ID") }}')
        self.client_secret = kwargs.get('client_secret') or os.getenv('{{ config.env_vars.get("client_secret", "CLIENT_SECRET") }}')
        self.access_token = kwargs.get('access_token')
        {% endif -%}
        
        self.tool_filter = kwargs.get('tool_filter')
        self._openapi_toolset = None
    
    def get_tools(self, readonly_context=None):
        """Get available tools"""
        if not self._openapi_toolset:
            self._openapi_toolset = self._create_openapi_toolset()
            self._configure_auth()
        
        return self._openapi_toolset.get_tools(readonly_context)
    
    def _create_openapi_toolset(self):
        """Create OpenAPI toolset"""
        spec_dict = self._fetch_spec()
        return OpenAPIToolset(
            spec_str=json.dumps(spec_dict),
            spec_str_type="json",
            tool_filter=self.tool_filter
        )
    
    def _fetch_spec(self):
        """Fetch OpenAPI specification"""
        response = requests.get(self.config['spec_url'])
        response.raise_for_status()
        return response.json()
    
    def _configure_auth(self):
        """Configure authentication"""
        {% if config.auth_type == "bearer" -%}
        if self.access_token:
            auth_credential = AuthCredential(
                auth_type=AuthCredentialTypes.HTTP,
                http=HttpAuth(
                    scheme="bearer",
                    credentials=HttpCredentials(token=self.access_token)
                )
            )
            self._openapi_toolset._configure_auth_all(None, auth_credential)
        {% endif -%}
    
    async def close(self):
        """Cleanup resources"""
        if self._openapi_toolset:
            await self._openapi_toolset.close()


def create_{{ api_name }}_toolset(**kwargs):
    """Factory function for {{ config.name }}"""
    return {{ class_name }}(**kwargs)
'''
        
        # Registry template
        registry_template = '''"""
Generated Toolset Registry
"""

from typing import Dict, Any, List

# Import all toolsets
{% for toolset in all_toolsets -%}
try:
    from .{{ toolset.module_name }} import {{ toolset.class_name }}, create_{{ toolset.api_name }}_toolset
except ImportError:
    {{ toolset.class_name }} = None
    create_{{ toolset.api_name }}_toolset = None

{% endfor %}

TOOLSET_REGISTRY = {
{% for toolset in all_toolsets -%}
    "{{ toolset.api_name }}": {{ toolset.class_name }},
{% endfor %}
}

def get_toolset(api_name: str, **kwargs):
    """Get toolset by name"""
    if api_name not in TOOLSET_REGISTRY:
        available = list(TOOLSET_REGISTRY.keys())
        raise ValueError(f"Unknown API: {api_name}. Available: {available}")
    
    toolset_class = TOOLSET_REGISTRY[api_name]
    if toolset_class is None:
        raise ImportError(f"Could not import toolset for {api_name}")
    
    return toolset_class(**kwargs)

def list_available_toolsets():
    """List available toolsets"""
    return [name for name, cls in TOOLSET_REGISTRY.items() if cls is not None]
'''
        
        # Save templates
        templates = {
            "toolsets/base_toolset.py.j2": base_toolset_template,
            "registry/__init__.py.j2": registry_template
        }
        
        for template_path, template_content in templates.items():
            file_path = self.toolset_configs_dir / "templates" / template_path
            with open(file_path, 'w') as f:
                f.write(template_content)
            print(f"  📄 Created template {file_path}")
    
    def create_processors(self):
        """Create processor modules"""
        # Create __init__.py for processors package
        init_content = '''"""
OpenAPI Spec Processors Package
"""

from .google_processor import GoogleSpecProcessor
from .atlassian_processor import AtlassianSpecProcessor
from .slack_processor import SlackSpecProcessor
from .salesforce_processor import SalesforceSpecProcessor
from .generic_processor import GenericSpecProcessor

__all__ = [
    'GoogleSpecProcessor',
    'AtlassianSpecProcessor', 
    'SlackSpecProcessor',
    'SalesforceSpecProcessor',
    'GenericSpecProcessor'
]
'''
        
        # Create basic processor files
        processor_template = '''"""
{provider} API Spec Processor
"""

from typing import Dict, Any
from .base_processor import SpecProcessor


class {class_name}(SpecProcessor):
    """Processor for {provider} APIs"""
    
    def supports_provider(self, provider: str) -> bool:
        return provider.lower() == "{provider_lower}"
    
    def process_spec(self, spec_dict: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process {provider} OpenAPI specification"""
        # Add {provider}-specific processing here
        return spec_dict
'''
        
        base_processor = '''"""
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
'''
        
        # Create processor files
        processors_dir = self.toolset_configs_dir / "processors"
        
        # Base processor
        with open(processors_dir / "base_processor.py", 'w') as f:
            f.write(base_processor)
        
        # Package init
        with open(processors_dir / "__init__.py", 'w') as f:
            f.write(init_content)
        
        # Individual processors
        providers = [
            ("google", "GoogleSpecProcessor"),
            ("atlassian", "AtlassianSpecProcessor"),
            ("slack", "SlackSpecProcessor"),
            ("salesforce", "SalesforceSpecProcessor"),
            ("generic", "GenericSpecProcessor")
        ]
        
        for provider, class_name in providers:
            content = processor_template.format(
                provider=provider.title(),
                class_name=class_name,
                provider_lower=provider
            )
            with open(processors_dir / f"{provider}_processor.py", 'w') as f:
                f.write(content)
            print(f"  📄 Created processor {provider}_processor.py")
    
    def setup_cli(self):
        """Set up CLI tool"""
        cli_script = '''#!/usr/bin/env python3
"""
Dynamic API Toolset Generator CLI
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from refactored_generator import CLIInterface


def main():
    parser = argparse.ArgumentParser(description="Dynamic API Toolset Generator")
    parser.add_argument("--config-dir", default="toolset_configs")
    
    subparsers = parser.add_subparsers(dest="command")
    
    # Init command
    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--force", action="store_true")
    
    # List command
    subparsers.add_parser("list")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate")
    gen_parser.add_argument("--provider")
    gen_parser.add_argument("--api")
    gen_parser.add_argument("--output", default="generated_toolsets")
    
    args = parser.parse_args()
    
    cli = CLIInterface(Path(args.config_dir))
    
    if args.command == "init":
        cli.init_project(getattr(args, 'force', False))
    elif args.command == "list":
        cli.list_providers()
    elif args.command == "generate":
        cli.generate(args.provider, args.api, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
'''
        
        cli_file = self.project_root / "scripts" / "toolset-cli.py"
        with open(cli_file, 'w') as f:
            f.write(cli_script)
        
        # Make executable
        cli_file.chmod(0o755)
        print(f"  📄 Created CLI script {cli_file}")
    
    def create_examples(self):
        """Create example files"""
        # Environment variables example
        env_example = '''# Dynamic API Toolset Generator Environment Variables
# Copy this to .env and fill in your actual values

# Google APIs
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_PROJECT_ID=your-google-project-id

# Slack
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token

# Atlassian
JIRA_CLIENT_ID=your-jira-client-id
JIRA_CLIENT_SECRET=your-jira-client-secret
JIRA_CLOUD_ID=your-atlassian-cloud-id

# Salesforce
SALESFORCE_CLIENT_ID=your-salesforce-client-id
SALESFORCE_CLIENT_SECRET=your-salesforce-client-secret
SALESFORCE_INSTANCE=your-instance-name
'''
        
        # Usage example
        usage_example = '''"""
Dynamic API Toolset Generator - Usage Example
"""

import asyncio
from pathlib import Path
from refactored_generator import ToolsetGenerator

async def main():
    # Initialize the generator
    generator = ToolsetGenerator(Path("toolset_configs"))
    
    # Generate all toolsets
    print("Generating toolsets...")
    results = generator.generate_all_toolsets(Path("generated_toolsets"))
    
    # Import and use a toolset
    import sys
    sys.path.append("generated_toolsets")
    
    try:
        from generated_toolsets import get_toolset
        
        # Create a Google Calendar toolset
        calendar_toolset = get_toolset(
            "google_calendar",
            client_id="your-client-id",
            client_secret="your-client-secret"
        )
        
        # Get available tools
        tools = calendar_toolset.get_tools()
        print(f"Generated {len(tools)} tools for Google Calendar")
        
    except ImportError as e:
        print(f"Could not import generated toolsets: {e}")
        print("Make sure to run the generator first!")

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        # Agent example
        agent_example = '''"""
Example ADK Agent using Generated Toolsets
"""

from google.adk.agents import LlmAgent
from generated_toolsets import get_toolset

def create_productivity_agent():
    """Create a productivity agent with multiple toolsets"""
    
    # Create toolsets
    toolsets = []
    
    # Google Calendar
    try:
        calendar_toolset = get_toolset("google_calendar")
        toolsets.append(calendar_toolset)
        print("✅ Added Google Calendar toolset")
    except Exception as e:
        print(f"⚠️ Could not add Google Calendar: {e}")
    
    # Slack
    try:
        slack_toolset = get_toolset("slack_web_api") 
        toolsets.append(slack_toolset)
        print("✅ Added Slack toolset")
    except Exception as e:
        print(f"⚠️ Could not add Slack: {e}")
    
    # Create the agent
    if toolsets:
        agent = LlmAgent(
            name="productivity_assistant",
            model="gemini-2.0-flash",
            description="Productivity assistant with calendar and communication tools",
            tools=toolsets,
            instruction="Help users manage their schedule and communications efficiently."
        )
        
        print(f"🤖 Created agent with {len(toolsets)} toolsets")
        return agent
    else:
        print("❌ No toolsets available - check your configuration")
        return None

if __name__ == "__main__":
    agent = create_productivity_agent()
    if agent:
        print("Agent ready for use!")
'''
        
        # Save examples
        examples = {
            ".env.example": env_example,
            "usage_example.py": usage_example,
            "agent_example.py": agent_example
        }
        
        for filename, content in examples.items():
            file_path = self.project_root / "examples" / filename
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"  📄 Created example {file_path}")
    
    def initial_generation(self):
        """Run initial toolset generation"""
        try:
            from toolset_configs.generator import ToolsetGenerator
            
            generator = ToolsetGenerator(self.toolset_configs_dir)
            results = generator.generate_all_toolsets(self.generated_dir)
            
            total_generated = sum(len(files) for files in results.values())
            print(f"  ✅ Generated {total_generated} toolsets across {len(results)} providers")
            
        except Exception as e:
            print(f"  ⚠️ Could not run initial generation: {e}")
            print("  💡 You can run generation manually later")
    
    def create_documentation(self):
        """Create documentation files"""
        readme = '''# Dynamic API Toolset Generator

A scalable, refactored system for generating Google Agent Development Kit (ADK) compatible toolsets from OpenAPI specifications.

## Features

- 🏗️ **Modular Architecture**: Decoupled components for maximum flexibility
- 📝 **Template-Based**: Jinja2 templates for code generation
- 🔧 **Provider-Specific**: Specialized processors for different API providers
- 🎯 **Multiple Auth Types**: OAuth2, Bearer tokens, API keys
- 📊 **Rich CLI**: Comprehensive command-line interface
- 🔍 **Validation**: Built-in configuration and toolset validation

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize the project:**
   ```bash
   python scripts/toolset-cli.py init
   ```

3. **Configure your APIs:**
   - Copy `examples/.env.example` to `.env`
   - Fill in your API credentials

4. **Generate toolsets:**
   ```bash
   python scripts/toolset-cli.py generate
   ```

5. **Use in your ADK agents:**
   ```python
   from generated_toolsets import get_toolset
   
   calendar_toolset = get_toolset("google_calendar", 
                                 client_id="your-id",
                                 client_secret="your-secret")
   ```

## Architecture

```
toolset_configs/
├── providers/           # API configurations by provider
│   ├── google/
│   ├── atlassian/
│   ├── slack/
│   └── salesforce/
├── templates/           # Jinja2 templates
│   ├── toolsets/
│   ├── auth/
│   └── registry/
└── processors/          # Provider-specific processors

generated_toolsets/      # Generated Python modules
├── google_calendar_toolset.py
├── slack_web_api_toolset.py
└── __init__.py         # Registry

examples/                # Usage examples
docs/                   # Documentation  
scripts/                # CLI tools
```

## CLI Commands

- `toolset-cli.py init` - Initialize new project
- `toolset-cli.py list` - List available providers and APIs
- `toolset-cli.py generate` - Generate toolsets
- `toolset-cli.py validate` - Validate configurations
- `toolset-cli.py test <provider> <api>` - Test specific toolset

## Supported Providers

- **Google Workspace**: Calendar, Drive, Gmail
- **Atlassian**: Jira, Confluence  
- **Slack**: Web API
- **Salesforce**: REST API
- **Microsoft**: Graph API
- **GitHub**: REST API
- **And many more...**

## Adding New APIs

1. Create configuration file:
   ```bash
   toolset-cli.py create-config myapi \\
     --provider custom \\
     --base-url https://api.example.com \\
     --spec-url https://api.example.com/openapi.json \\
     --auth-type bearer
   ```

2. Generate toolset:
   ```bash
   toolset-cli.py generate --provider custom --api myapi
   ```

## Contributing

1. Add your API configuration in `toolset_configs/providers/`
2. Create processor if needed in `toolset_configs/processors/`
3. Test with `toolset-cli.py test`
4. Submit pull request

## License

MIT License - see LICENSE file for details.
'''
        
        architecture_doc = '''# Architecture Documentation

## Overview

The Dynamic API Toolset Generator uses a modular, plugin-based architecture that separates concerns and enables easy extension.

## Core Components

### 1. Configuration Manager (`ConfigManager`)
- Loads YAML configuration files by provider
- Validates configuration structure
- Manages provider-specific settings

### 2. Template Renderer (`TemplateRenderer`)
- Jinja2-based template rendering
- Custom filters for naming conventions
- Extensible template system

### 3. Spec Processors (`SpecProcessor`)
- Provider-specific OpenAPI processing
- Handles API quirks and customizations
- Pluggable processor architecture

### 4. Toolset Generator (`ToolsetGenerator`)
- Orchestrates the generation process
- Combines configuration, templates, and processors
- Outputs ADK-compatible Python modules

## Data Flow

```
Configuration Files → Config Manager → Template Context
                                           ↓
OpenAPI Specs → Spec Processors → Template Renderer → Generated Code
```

## Extension Points

### Adding New Providers

1. **Configuration**: Create YAML files in `providers/newprovider/`
2. **Processor**: Implement `SpecProcessor` for provider-specific logic
3. **Templates**: Customize templates if needed

### Custom Authentication

Extend the base template or create provider-specific auth templates.

### Custom Processors

```python
class CustomProcessor(SpecProcessor):
    def supports_provider(self, provider: str) -> bool:
        return provider == "custom"
    
    def process_spec(self, spec_dict, config):
        # Custom processing logic
        return spec_dict
```

## Testing Strategy

1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test end-to-end generation
3. **Validation Tests**: Test generated toolsets
4. **CLI Tests**: Test command-line interface

## Performance Considerations

- Lazy loading of configurations
- Caching of OpenAPI specifications
- Efficient template rendering
- Parallel generation for multiple providers
'''
        
        # Save documentation
        docs = {
            "README.md": readme,
            "ARCHITECTURE.md": architecture_doc
        }
        
        for filename, content in docs.items():
            file_path = self.project_root / "docs" / filename
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"  📄 Created documentation {file_path}")
        
        # Also create root README
        with open(self.project_root / "README.md", 'w') as f:
            f.write(readme)
    
    def print_next_steps(self):
        """Print next steps for the user"""
        print(f"""
🎯 Next Steps:

1. **Configure your APIs:**
   cd {self.project_root}
   cp examples/.env.example .env
   # Edit .env with your API credentials

2. **Generate toolsets:**
   python scripts/toolset-cli.py generate

3. **Test a toolset:**
   python scripts/toolset-cli.py test google calendar

4. **Use in your agents:**
   python examples/agent_example.py

5. **Add custom APIs:**
   python scripts/toolset-cli.py create-config myapi --provider custom --base-url https://api.example.com --spec-url https://api.example.com/openapi.json --auth-type bearer

📚 Documentation: docs/README.md
🔧 CLI Help: python scripts/toolset-cli.py --help
💡 Examples: examples/
        """)


def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Dynamic API Toolset Generator")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd(),
                       help="Project directory (default: current directory)")
    parser.add_argument("--skip-deps", action="store_true",
                       help="Skip dependency installation")
    
    args = parser.parse_args()
    
    try:
        setup = SetupManager(args.project_dir)
        
        if args.skip_deps:
            setup.install_dependencies = lambda: print("  ⏭️ Skipping dependency installation")
        
        setup.run_complete_setup()
        
    except KeyboardInterrupt:
        print("\n⚠️ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()