"""
Dynamic API Toolset Generator for Google Agent Development Kit (ADK)
====================================================================

This module provides a framework for dynamically generating toolsets for various APIs
using Jinja2 templating and configuration files. It supports Google Workspace, Atlassian,
Slack, Salesforce, and other APIs through OpenAPI specifications.

Based on Google's Agent Development Kit (ADK) framework which is designed for building
multi-agent AI systems with precise control over agent behavior and tool orchestration.
"""

import json
import yaml
import os
import requests
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import jinja2
from urllib.parse import urljoin

from google.adk.tools.base_toolset import BaseToolset, ToolPredicate
from google.adk.tools.openapi_tool import OpenAPIToolset
from google.adk.auth.auth_credential import AuthCredential, AuthCredentialTypes, HttpAuth, HttpCredentials, OAuth2Auth
from google.adk.auth import OpenIdConnectWithConfig
from fastapi.openapi.models import OAuth2, OAuthFlowAuthorizationCode, OAuthFlows


@dataclass
class APIConfig:
    """Configuration for an API provider"""
    name: str
    base_url: str
    spec_url: str
    auth_type: str  # "oauth2", "bearer", "api_key"
    scopes: Dict[str, str] = field(default_factory=dict)
    auth_endpoints: Dict[str, str] = field(default_factory=dict)
    custom_headers: Dict[str, str] = field(default_factory=dict)
    server_url_template: Optional[str] = None
    env_vars: Dict[str, str] = field(default_factory=dict)


class DynamicAPIToolsetGenerator:
    """
    Dynamic toolset generator that creates ADK-compatible toolsets from configuration
    """
    
    def __init__(self, config_dir: str = "api_configs"):
        self.config_dir = Path(config_dir)
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.config_dir / "templates")),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        self._api_configs = self._load_api_configs()
    
    def _load_api_configs(self) -> Dict[str, APIConfig]:
        """Load API configurations from YAML files"""
        configs = {}
        config_path = self.config_dir / "apis"
        
        if not config_path.exists():
            self._create_default_configs()
            
        for config_file in config_path.glob("*.yaml"):
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
                api_name = config_file.stem
                configs[api_name] = APIConfig(**config_data)
        
        return configs
    
    def _create_default_configs(self):
        """Create default API configurations"""
        self.config_dir.mkdir(exist_ok=True)
        apis_dir = self.config_dir / "apis"
        apis_dir.mkdir(exist_ok=True)
        templates_dir = self.config_dir / "templates"
        templates_dir.mkdir(exist_ok=True)
        
        # Create default API configurations
        default_configs = {
            "google_calendar": {
                "name": "Google Calendar API",
                "base_url": "https://www.googleapis.com/calendar/v3",
                "spec_url": "https://raw.githubusercontent.com/googleapis/google-api-specification/main/calendar/v3/calendar-v3.json",
                "auth_type": "oauth2",
                "scopes": {
                    "read": "https://www.googleapis.com/auth/calendar.readonly",
                    "write": "https://www.googleapis.com/auth/calendar"
                },
                "auth_endpoints": {
                    "authorization_url": "https://accounts.google.com/o/oauth2/auth",
                    "token_url": "https://oauth2.googleapis.com/token"
                },
                "env_vars": {
                    "client_id": "GOOGLE_CLIENT_ID",
                    "client_secret": "GOOGLE_CLIENT_SECRET"
                }
            },
            "google_drive": {
                "name": "Google Drive API",
                "base_url": "https://www.googleapis.com/drive/v3",
                "spec_url": "https://raw.githubusercontent.com/googleapis/google-api-specification/main/drive/v3/drive-v3.json",
                "auth_type": "oauth2",
                "scopes": {
                    "read": "https://www.googleapis.com/auth/drive.readonly",
                    "write": "https://www.googleapis.com/auth/drive"
                },
                "auth_endpoints": {
                    "authorization_url": "https://accounts.google.com/o/oauth2/auth",
                    "token_url": "https://oauth2.googleapis.com/token"
                },
                "env_vars": {
                    "client_id": "GOOGLE_CLIENT_ID",
                    "client_secret": "GOOGLE_CLIENT_SECRET"
                }
            },
            "slack": {
                "name": "Slack Web API",
                "base_url": "https://slack.com/api",
                "spec_url": "https://raw.githubusercontent.com/slackapi/slack-api-specs/master/web-api/slack_web_openapi_v2.json",
                "auth_type": "bearer",
                "scopes": {
                    "read": "users:read,channels:read,chat:read",
                    "write": "chat:write,channels:write"
                },
                "env_vars": {
                    "access_token": "SLACK_BOT_TOKEN"
                }
            },
            "jira": {
                "name": "Atlassian Jira API",
                "base_url": "https://api.atlassian.com/ex/jira/{cloud_id}",
                "spec_url": "https://developer.atlassian.com/cloud/jira/platform/swagger-v3.v3.json",
                "auth_type": "oauth2",
                "scopes": {
                    "read": "read:jira-user,read:jira-work",
                    "write": "write:jira-work,read:jira-work"
                },
                "auth_endpoints": {
                    "authorization_url": "https://auth.atlassian.com/authorize",
                    "token_url": "https://auth.atlassian.com/oauth/token"
                },
                "server_url_template": "https://api.atlassian.com/ex/jira/{{ cloud_id }}",
                "env_vars": {
                    "client_id": "JIRA_CLIENT_ID",
                    "client_secret": "JIRA_CLIENT_SECRET",
                    "cloud_id": "JIRA_CLOUD_ID"
                }
            },
            "confluence": {
                "name": "Atlassian Confluence API",
                "base_url": "https://api.atlassian.com/ex/confluence/{cloud_id}",
                "spec_url": "https://developer.atlassian.com/cloud/confluence/swagger.v3.json",
                "auth_type": "oauth2",
                "scopes": {
                    "read": "read:confluence-content.all",
                    "write": "write:confluence-content,read:confluence-content.all"
                },
                "auth_endpoints": {
                    "authorization_url": "https://auth.atlassian.com/authorize",
                    "token_url": "https://auth.atlassian.com/oauth/token"
                },
                "server_url_template": "https://api.atlassian.com/ex/confluence/{{ cloud_id }}",
                "env_vars": {
                    "client_id": "CONFLUENCE_CLIENT_ID",
                    "client_secret": "CONFLUENCE_CLIENT_SECRET",
                    "cloud_id": "CONFLUENCE_CLOUD_ID"
                }
            },
            "salesforce": {
                "name": "Salesforce REST API",
                "base_url": "https://{instance}.salesforce.com/services/data/v58.0",
                "spec_url": "custom://salesforce_openapi_spec",  # Custom generator needed
                "auth_type": "oauth2",
                "scopes": {
                    "api": "api",
                    "refresh_token": "refresh_token"
                },
                "auth_endpoints": {
                    "authorization_url": "https://login.salesforce.com/services/oauth2/authorize",
                    "token_url": "https://login.salesforce.com/services/oauth2/token"
                },
                "server_url_template": "https://{{ instance }}.salesforce.com/services/data/v58.0",
                "env_vars": {
                    "client_id": "SALESFORCE_CLIENT_ID",
                    "client_secret": "SALESFORCE_CLIENT_SECRET",
                    "instance": "SALESFORCE_INSTANCE"
                }
            }
        }
        
        for api_name, config in default_configs.items():
            config_file = apis_dir / f"{api_name}.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
        
        # Create the base toolset template
        base_template = \
'''"""
{{ config.name }} Toolset
Generated dynamically for Google Agent Development Kit (ADK)
"""

import json
import os
import requests
from typing import Any, List, Optional, Union

from typing_extensions import override
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.base_toolset import BaseToolset, ToolPredicate
from google.adk.tools.openapi_tool import OpenAPIToolset
from google.adk.auth.auth_credential import AuthCredential, AuthCredentialTypes, HttpAuth, HttpCredentials, OAuth2Auth
from google.adk.auth import OpenIdConnectWithConfig
from fastapi.openapi.models import OAuth2, OAuthFlowAuthorizationCode, OAuthFlows


class {{ class_name }}(BaseToolset):
    """
    {{ config.name }} toolset using OpenAPI spec and ADK authentication
    """

    def __init__(
        self,
{%- if config.auth_type == "bearer" %}
        access_token: Optional[str] = None,
{%- elif config.auth_type == "oauth2" %}
        access_token: Optional[str] = None,
{%- endif %}
        tool_filter: Optional[Union[ToolPredicate, List[str]]] = None,
{%- for key, env_var in config.env_vars.items() %}
        {{ key }}: Optional[str] = None,
{%- endfor %}
    ):
        self.config = {{ config_dict }}
{%- if config.auth_type == "bearer" %}
        self.access_token = access_token or os.getenv("{{ config.env_vars.get('access_token', 'ACCESS_TOKEN') }}")
{%- elif config.auth_type == "oauth2" %}
        self.access_token = access_token
{%- endif %}
{%- for key, env_var in config.env_vars.items() %}
        self.{{ key }} = {{ key }} or os.getenv("{{ env_var }}")
{%- endfor %}
        self.tool_filter = tool_filter
        self._openapi_toolset = None

    @override
    def get_tools(
        self,
        readonly_context: Optional[ReadonlyContext] = None
    ) -> List[Any]:
        if not self._openapi_toolset:
            self._openapi_toolset = self._load_toolset()
        
{%- if config.auth_type == "oauth2" %}
        # Configure OAuth2 authentication
        auth_credential = self._create_oauth2_credential()
        oidc = self._create_oidc_config()
        self._openapi_toolset._configure_auth_all(oidc, auth_credential)
{%- elif config.auth_type == "bearer" %}
        # Configure Bearer token authentication
        auth_credential = self._create_bearer_credential()
        self._openapi_toolset._configure_auth_all(None, auth_credential)
{%- endif %}
        
        return self._openapi_toolset.get_tools(readonly_context)

    def _load_toolset(self) -> OpenAPIToolset:
        """Load the OpenAPI specification and create toolset"""
        spec_dict = self._fetch_openapi_spec()
        
{%- if config.server_url_template %}
        # Update server URLs if template provided
        server_url = self._render_server_url()
        spec_dict['servers'] = [{'url': server_url}]
{%- endif %}
        
        # Process boolean enums
        self._convert_boolean_enums(spec_dict)
        
        return OpenAPIToolset(
            spec_str=json.dumps(spec_dict),
            spec_str_type="json",
            tool_filter=self.tool_filter,
        )

    def _fetch_openapi_spec(self) -> dict:
        """Fetch and return the OpenAPI specification"""
{%- if config.spec_url.startswith('custom://') %}
        # Custom spec generation logic
        return self._generate_custom_spec()
{%- else %}
        response = requests.get("{{ config.spec_url }}")
        response.raise_for_status()
        return response.json()
{%- endif %}

{%- if config.server_url_template %}

    def _render_server_url(self) -> str:
        """Render server URL from template with environment variables"""
        template_vars = {}
{%- for key, env_var in config.env_vars.items() %}
        template_vars["{{ key }}"] = getattr(self, "{{ key }}", None)
{%- endfor %}
        
        from jinja2 import Template
        template = Template("{{ config.server_url_template }}")
        return template.render(**template_vars)
{%- endif %}

{%- if config.auth_type == "oauth2" %}

    def _create_oauth2_credential(self) -> AuthCredential:
        """Create OAuth2 authentication credential"""
        if self.access_token:
            return AuthCredential(
                auth_type=AuthCredentialTypes.HTTP,
                http=HttpAuth(
                    scheme="bearer",
                    credentials=HttpCredentials(token=self.access_token),
                ),
            )
        else:
            return AuthCredential(
                auth_type=AuthCredentialTypes.OAUTH2,
                oauth2=OAuth2Auth(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                )
            )

    def _create_oidc_config(self) -> OpenIdConnectWithConfig:
        """Create OpenID Connect configuration"""
        return OpenIdConnectWithConfig(
            authorization_endpoint="{{ config.auth_endpoints.get('authorization_url', '') }}",
            token_endpoint="{{ config.auth_endpoints.get('token_url', '') }}",
            userinfo_endpoint="{{ config.auth_endpoints.get('userinfo_url', '') }}",
            revocation_endpoint="{{ config.auth_endpoints.get('revocation_url', '') }}",
            token_endpoint_auth_methods_supported=["client_secret_post", "client_secret_basic"],
            grant_types_supported=["authorization_code"],
            scopes=list(self.config["scopes"].values())
        )
{%- elif config.auth_type == "bearer" %}

    def _create_bearer_credential(self) -> AuthCredential:
        """Create Bearer token authentication credential"""
        return AuthCredential(
            auth_type=AuthCredentialTypes.HTTP,
            http=HttpAuth(
                scheme="bearer",
                credentials=HttpCredentials(token=self.access_token),
            ),
        )
{%- endif %}

{%- if config.spec_url.startswith('custom://') %}

    def _generate_custom_spec(self) -> dict:
        """Generate custom OpenAPI specification"""
        # Implement custom spec generation logic here
        # This is particularly useful for APIs like Salesforce that don't provide
        # a comprehensive OpenAPI spec
        raise NotImplementedError("Custom spec generation not implemented for {{ config.name }}")
{%- endif %}

    @staticmethod
    def _convert_boolean_enums(obj):
        """Convert boolean enums to strings in the OpenAPI spec"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == 'enum' and any(isinstance(x, bool) for x in value):
                    obj[key] = [str(x).lower() for x in value]
                elif isinstance(value, (dict, list)):
                    {{ class_name }}._convert_boolean_enums(value)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    {{ class_name }}._convert_boolean_enums(item)
    
    async def close(self):
        """Cleanup resources"""
        if self._openapi_toolset:
            await self._openapi_toolset.close()


# Convenience factory function
def create_{{ api_name }}_toolset(**kwargs) -> {{ class_name }}:
    """Create a {{ config.name }} toolset with default configuration"""
    return {{ class_name }}(**kwargs)
'''
        template_file = templates_dir / "base_toolset.py.j2"
        with open(template_file, 'w') as f:
            f.write(base_template)
    
    def generate_toolset(self, api_name: str, output_dir: str = "generated_toolsets") -> str:
        """Generate a toolset class for the specified API"""
        if api_name not in self._api_configs:
            raise ValueError(f"Unknown API: {api_name}. Available APIs: {list(self._api_configs.keys())}")
        
        config = self._api_configs[api_name]
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Prepare template variables
        class_name = f"{''.join(word.capitalize() for word in api_name.split('_'))}Toolset"
        template_vars = {
            'api_name': api_name,
            'class_name': class_name,
            'config': config,
            'config_dict': self._config_to_dict(config)
        }
        
        # Render the template
        template = self.template_env.get_template("base_toolset.py.j2")
        rendered_code = template.render(**template_vars)
        
        # Write the generated file
        output_file = output_path / f"{api_name}_toolset.py"
        with open(output_file, 'w') as f:
            f.write(rendered_code)
        
        return str(output_file)
    
    def _config_to_dict(self, config: APIConfig) -> str:
        """Convert APIConfig to a dictionary string for template"""
        config_dict = {
            'name': config.name,
            'base_url': config.base_url,
            'spec_url': config.spec_url,
            'auth_type': config.auth_type,
            'scopes': config.scopes,
            'auth_endpoints': config.auth_endpoints,
            'server_url_template': config.server_url_template,
            'env_vars': config.env_vars
        }
        return repr(config_dict)
    
    def list_available_apis(self) -> List[str]:
        """List all available API configurations"""
        return list(self._api_configs.keys())
    
    def generate_all_toolsets(self, output_dir: str = "generated_toolsets") -> List[str]:
        """Generate toolsets for all configured APIs"""
        generated_files = []
        for api_name in self._api_configs:
            try:
                file_path = self.generate_toolset(api_name, output_dir)
                generated_files.append(file_path)
                print(f"✓ Generated {api_name} toolset: {file_path}")
            except Exception as e:
                print(f"✗ Failed to generate {api_name} toolset: {e}")
        
        return generated_files
    
    def create_unified_toolset_registry(self, output_dir: str = "generated_toolsets") -> str:
        """Create a unified registry that imports all generated toolsets"""
        registry_content = '''"""
Unified Toolset Registry for Google Agent Development Kit (ADK)
Generated dynamically from API configurations
"""

# Import all generated toolsets
'''
        
        for api_name in self._api_configs:
            class_name = f"{''.join(word.capitalize() for word in api_name.split('_'))}Toolset"
            registry_content += f"from .{api_name}_toolset import {class_name}, create_{api_name}_toolset\n"
        
        registry_content += '''

# Registry of all available toolsets
TOOLSET_REGISTRY = {
'''
        
        for api_name in self._api_configs:
            class_name = f"{''.join(word.capitalize() for word in api_name.split('_'))}Toolset"
            registry_content += f'    "{api_name}": {class_name},\n'
        
        registry_content += '''}

# Factory functions registry
FACTORY_REGISTRY = {
'''
        
        for api_name in self._api_configs:
            registry_content += f'    "{api_name}": create_{api_name}_toolset,\n'
        
        registry_content += '''}


def get_toolset(api_name: str, **kwargs):
    """Get a toolset instance by API name"""
    if api_name not in TOOLSET_REGISTRY:
        raise ValueError(f"Unknown API: {api_name}. Available: {list(TOOLSET_REGISTRY.keys())}")
    
    return TOOLSET_REGISTRY[api_name](**kwargs)


def list_available_toolsets():
    """List all available toolset names"""
    return list(TOOLSET_REGISTRY.keys())
'''
        
        output_path = Path(output_dir)
        registry_file = output_path / "__init__.py"
        
        with open(registry_file, 'w') as f:
            f.write(registry_content)
        
        return str(registry_file)


# Example usage and testing
if __name__ == "__main__":
    # Create the generator
    generator = DynamicAPIToolsetGenerator()
    
    # List available APIs
    print("Available APIs:", generator.list_available_apis())
    
    # Generate all toolsets
    generated_files = generator.generate_all_toolsets()
    
    # Create unified registry
    registry_file = generator.create_unified_toolset_registry()
    print(f"Created registry: {registry_file}")
    
    print("\nGeneration complete! You can now use the generated toolsets in your ADK agents.")