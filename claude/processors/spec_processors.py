"""
Provider-Specific OpenAPI Processors
====================================

This module contains specialized processors for different API providers
to handle their specific OpenAPI specification requirements and customizations.
"""

import json
import os
import requests
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)


class SpecProcessor(ABC):
    """Abstract base class for OpenAPI spec processors"""
    
    @abstractmethod
    def process_spec(self, spec_dict: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process the OpenAPI specification"""
        pass

    @abstractmethod
    def supports_provider(self, provider: str) -> bool:
        """Check if this processor supports the given provider"""
        pass

    def generate_custom_spec(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate custom OpenAPI specification (optional override)"""
        raise NotImplementedError(f"Custom spec generation not implemented for {self.__class__.__name__}")


class GoogleSpecProcessor(SpecProcessor):
    """Processor for Google Workspace APIs"""
    
    def supports_provider(self, provider: str) -> bool:
        return provider.lower() in ["google", "google_workspace"]
    
    def process_spec(self, spec_dict: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process Google API OpenAPI specifications"""
        # Google APIs often use discovery format, convert if needed
        if "kind" in spec_dict and spec_dict["kind"] == "discovery#restDescription":
            spec_dict = self._convert_discovery_to_openapi(spec_dict)
        
        # Add Google-specific authentication schemes
        self._add_google_auth_schemes(spec_dict)
        
        # Handle Google-specific parameter formats
        self._process_google_parameters(spec_dict)
        
        return spec_dict
    
    def _convert_discovery_to_openapi(self, discovery_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Google Discovery format to OpenAPI 3.0"""
        openapi_spec = {
            "openapi": "3.0.3",
            "info": {
                "title": discovery_spec.get("title", "Google API"),
                "description": discovery_spec.get("description", ""),
                "version": discovery_spec.get("version", "1.0.0")
            },
            "servers": [
                {"url": discovery_spec.get("rootUrl", "") + discovery_spec.get("servicePath", "")}
            ],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {
                    "OAuth2": {
                        "type": "oauth2",
                        "flows": {
                            "authorizationCode": {
                                "authorizationUrl": "https://accounts.google.com/o/oauth2/auth",
                                "tokenUrl": "https://oauth2.googleapis.com/token",
                                "scopes": discovery_spec.get("auth", {}).get("oauth2", {}).get("scopes", {})
                            }
                        }
                    }
                }
            }
        }
        
        # Convert resources to paths
        if "resources" in discovery_spec:
            self._convert_resources_to_paths(discovery_spec["resources"], openapi_spec["paths"])
        
        # Convert schemas
        if "schemas" in discovery_spec:
            openapi_spec["components"]["schemas"] = discovery_spec["schemas"]
        
        return openapi_spec
    
    def _convert_resources_to_paths(self, resources: Dict[str, Any], paths: Dict[str, Any]):
        """Convert Google Discovery resources to OpenAPI paths"""
        for resource_name, resource in resources.items():
            if "methods" in resource:
                for method_name, method in resource["methods"].items():
                    path = method.get("path", f"/{resource_name}/{method_name}")
                    http_method = method.get("httpMethod", "GET").lower()
                    
                    if path not in paths:
                        paths[path] = {}
                    
                    paths[path][http_method] = {
                        "operationId": method.get("id", f"{resource_name}_{method_name}"),
                        "summary": method.get("description", ""),
                        "parameters": self._convert_parameters(method.get("parameters", {})),
                        "responses": {
                            "200": {
                                "description": "Successful response",
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
            
            # Handle nested resources
            if "resources" in resource:
                self._convert_resources_to_paths(resource["resources"], paths)
    
    def _convert_parameters(self, discovery_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert Google Discovery parameters to OpenAPI parameters"""
        openapi_params = []
        
        for param_name, param in discovery_params.items():
            openapi_param = {
                "name": param_name,
                "in": param.get("location", "query"),
                "required": param.get("required", False),
                "description": param.get("description", ""),
                "schema": {
                    "type": param.get("type", "string")
                }
            }
            
            if "enum" in param:
                openapi_param["schema"]["enum"] = param["enum"]
            
            openapi_params.append(openapi_param)
        
        return openapi_params
    
    def _add_google_auth_schemes(self, spec_dict: Dict[str, Any]):
        """Add Google-specific authentication schemes"""
        if "components" not in spec_dict:
            spec_dict["components"] = {}
        
        if "securitySchemes" not in spec_dict["components"]:
            spec_dict["components"]["securitySchemes"] = {}
        
        # Add Google OAuth2 scheme if not present
        if "OAuth2" not in spec_dict["components"]["securitySchemes"]:
            spec_dict["components"]["securitySchemes"]["OAuth2"] = {
                "type": "oauth2",
                "flows": {
                    "authorizationCode": {
                        "authorizationUrl": "https://accounts.google.com/o/oauth2/auth",
                        "tokenUrl": "https://oauth2.googleapis.com/token",
                        "scopes": {
                            "https://www.googleapis.com/auth/userinfo.email": "View your email address",
                            "https://www.googleapis.com/auth/userinfo.profile": "View your basic profile info"
                        }
                    }
                }
            }
    
    def _process_google_parameters(self, spec_dict: Dict[str, Any]):
        """Process Google-specific parameter formats"""
        # Handle quotaUser, userIp, and other Google standard parameters
        standard_params = {
            "quotaUser": {
                "name": "quotaUser",
                "in": "query",
                "description": "Available to use for quota purposes for server-side applications",
                "schema": {"type": "string"}
            },
            "userIp": {
                "name": "userIp", 
                "in": "query",
                "description": "IP address of the site where the request originates",
                "schema": {"type": "string"}
            },
            "alt": {
                "name": "alt",
                "in": "query",
                "description": "Data format for response",
                "schema": {
                    "type": "string",
                    "enum": ["json", "media", "proto"],
                    "default": "json"
                }
            }
        }
        
        # Add standard parameters to all operations
        if "paths" in spec_dict:
            for path, path_item in spec_dict["paths"].items():
                for method, operation in path_item.items():
                    if method in ["get", "post", "put", "delete", "patch", "head", "options"]:
                        if "parameters" not in operation:
                            operation["parameters"] = []
                        
                        # Add standard parameters if not already present
                        existing_params = {p["name"] for p in operation["parameters"]}
                        for param_name, param_def in standard_params.items():
                            if param_name not in existing_params:
                                operation["parameters"].append(param_def.copy())


class AtlassianSpecProcessor(SpecProcessor):
    """Processor for Atlassian APIs (Jira, Confluence)"""
    
    def supports_provider(self, provider: str) -> bool:
        return provider.lower() == "atlassian"
    
    def process_spec(self, spec_dict: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process Atlassian API OpenAPI specifications"""
        # Handle Atlassian Cloud ID in server URLs
        self._update_server_urls_for_cloud(spec_dict, config)
        
        # Convert boolean enums (Atlassian specific issue)
        self._convert_boolean_enums(spec_dict)
        
        # Add Atlassian-specific authentication
        self._add_atlassian_auth_schemes(spec_dict)
        
        # Process Atlassian-specific response formats
        self._process_atlassian_responses(spec_dict)
        
        return spec_dict
    
    def _update_server_urls_for_cloud(self, spec_dict: Dict[str, Any], config: Dict[str, Any]):
        """Update server URLs for Atlassian Cloud"""
        cloud_id = config.get("env_vars", {}).get("cloud_id")
        if cloud_id and "servers" not in spec_dict:
            base_url = config.get("base_url", "")
            if "{cloud_id}" in base_url:
                server_url = base_url.replace("{cloud_id}", cloud_id)
                spec_dict["servers"] = [{"url": server_url}]
    
    def _convert_boolean_enums(self, obj):
        """Convert boolean enums to strings (Atlassian APIs issue)"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == 'enum' and isinstance(value, list):
                    if any(isinstance(x, bool) for x in value):
                        obj[key] = [str(x).lower() if isinstance(x, bool) else x for x in value]
                elif isinstance(value, (dict, list)):
                    self._convert_boolean_enums(value)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    self._convert_boolean_enums(item)
    
    def _add_atlassian_auth_schemes(self, spec_dict: Dict[str, Any]):
        """Add Atlassian-specific authentication schemes"""
        if "components" not in spec_dict:
            spec_dict["components"] = {}
        
        if "securitySchemes" not in spec_dict["components"]:
            spec_dict["components"]["securitySchemes"] = {}
        
        # Atlassian OAuth2
        spec_dict["components"]["securitySchemes"]["OAuth2"] = {
            "type": "oauth2",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": "https://auth.atlassian.com/authorize",
                    "tokenUrl": "https://auth.atlassian.com/oauth/token",
                    "scopes": {
                        "read:jira-user": "View user information in Jira",
                        "read:jira-work": "Read project and issue data in Jira",
                        "write:jira-work": "Create and edit issues in Jira",
                        "read:confluence-content.all": "View Confluence content",
                        "write:confluence-content": "Create and edit Confluence content"
                    }
                }
            }
        }
    
    def _process_atlassian_responses(self, spec_dict: Dict[str, Any]):
        """Process Atlassian-specific response formats"""
        # Add common Atlassian error responses
        common_errors = {
            "400": {
                "description": "Bad Request - The request was invalid",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "errorMessages": {"type": "array", "items": {"type": "string"}},
                                "errors": {"type": "object"}
                            }
                        }
                    }
                }
            },
            "401": {
                "description": "Unauthorized - Authentication required",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "message": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "403": {
                "description": "Forbidden - Insufficient permissions",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "message": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
        
        # Add error responses to all operations
        if "paths" in spec_dict:
            for path, path_item in spec_dict["paths"].items():
                for method, operation in path_item.items():
                    if method in ["get", "post", "put", "delete", "patch"]:
                        if "responses" not in operation:
                            operation["responses"] = {}
                        
                        # Add common error responses if not present
                        for status_code, error_response in common_errors.items():
                            if status_code not in operation["responses"]:
                                operation["responses"][status_code] = error_response.copy()


class SlackSpecProcessor(SpecProcessor):
    """Processor for Slack Web API"""
    
    def supports_provider(self, provider: str) -> bool:
        return provider.lower() == "slack"
    
    def process_spec(self, spec_dict: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process Slack API OpenAPI specifications"""
        # Handle Slack's OpenAPI 2.0 format and upgrade to 3.0
        if spec_dict.get("swagger") == "2.0":
            spec_dict = self._upgrade_to_openapi_3(spec_dict)
        
        # Add Slack-specific authentication
        self._add_slack_auth_schemes(spec_dict)
        
        # Process Slack-specific response formats
        self._process_slack_responses(spec_dict)
        
        # Handle Slack rate limiting information
        self._add_rate_limiting_info(spec_dict)
        
        return spec_dict
    
    def _upgrade_to_openapi_3(self, swagger_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Upgrade Slack's OpenAPI 2.0 spec to 3.0"""
        openapi_spec = {
            "openapi": "3.0.3",
            "info": swagger_spec.get("info", {}),
            "servers": [],
            "paths": swagger_spec.get("paths", {}),
            "components": {
                "schemas": swagger_spec.get("definitions", {}),
                "securitySchemes": {}
            }
        }
        
        # Convert host and basePath to servers
        host = swagger_spec.get("host", "slack.com")
        base_path = swagger_spec.get("basePath", "/api")
        scheme = swagger_spec.get("schemes", ["https"])[0]
        
        openapi_spec["servers"] = [
            {"url": f"{scheme}://{host}{base_path}"}
        ]
        
        # Convert security definitions
        if "securityDefinitions" in swagger_spec:
            for name, security_def in swagger_spec["securityDefinitions"].items():
                if security_def.get("type") == "oauth2":
                    openapi_spec["components"]["securitySchemes"][name] = {
                        "type": "oauth2",
                        "flows": {
                            "authorizationCode": {
                                "authorizationUrl": security_def.get("authorizationUrl", ""),
                                "tokenUrl": security_def.get("tokenUrl", ""),
                                "scopes": security_def.get("scopes", {})
                            }
                        }
                    }
        
        # Update parameter references and formats
        self._update_parameter_formats(openapi_spec)
        
        return openapi_spec
    
    def _update_parameter_formats(self, spec_dict: Dict[str, Any]):
        """Update parameter formats for OpenAPI 3.0"""
        if "paths" not in spec_dict:
            return
        
        for path, path_item in spec_dict["paths"].items():
            for method, operation in path_item.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    # Convert form parameters to requestBody for POST operations
                    if method == "post" and "parameters" in operation:
                        form_params = [p for p in operation["parameters"] 
                                     if p.get("in") == "formData"]
                        
                        if form_params:
                            # Create requestBody from form parameters
                            properties = {}
                            required = []
                            
                            for param in form_params:
                                properties[param["name"]] = {
                                    "type": param.get("type", "string"),
                                    "description": param.get("description", "")
                                }
                                if param.get("required", False):
                                    required.append(param["name"])
                            
                            operation["requestBody"] = {
                                "content": {
                                    "application/x-www-form-urlencoded": {
                                        "schema": {
                                            "type": "object",
                                            "properties": properties,
                                            "required": required
                                        }
                                    }
                                }
                            }
                            
                            # Remove form parameters from parameters list
                            operation["parameters"] = [p for p in operation["parameters"] 
                                                     if p.get("in") != "formData"]
    
    def _add_slack_auth_schemes(self, spec_dict: Dict[str, Any]):
        """Add Slack-specific authentication schemes"""
        if "components" not in spec_dict:
            spec_dict["components"] = {}
        
        if "securitySchemes" not in spec_dict["components"]:
            spec_dict["components"]["securitySchemes"] = {}
        
        # Slack Bot Token
        spec_dict["components"]["securitySchemes"]["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "description": "Slack Bot Token (starts with xoxb-)"
        }
        
        # Slack OAuth2
        spec_dict["components"]["securitySchemes"]["SlackOAuth"] = {
            "type": "oauth2",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": "https://slack.com/oauth/v2/authorize",
                    "tokenUrl": "https://slack.com/api/oauth.v2.access",
                    "scopes": {
                        "channels:read": "View basic information about public channels",
                        "channels:write": "Manage public channels",
                        "chat:write": "Send messages as the app",
                        "chat:write.public": "Send messages to channels the app isn't a member of",
                        "users:read": "View people in a workspace",
                        "files:read": "View files shared in channels and conversations",
                        "files:write": "Upload, edit, and delete files"
                    }
                }
            }
        }
    
    def _process_slack_responses(self, spec_dict: Dict[str, Any]):
        """Process Slack-specific response formats"""
        # Slack APIs always return JSON with 'ok' field
        slack_success_schema = {
            "type": "object",
            "properties": {
                "ok": {"type": "boolean", "enum": [True]},
                "data": {"type": "object"}
            },
            "required": ["ok"]
        }
        
        slack_error_schema = {
            "type": "object",
            "properties": {
                "ok": {"type": "boolean", "enum": [False]},
                "error": {"type": "string"},
                "warning": {"type": "string"}
            },
            "required": ["ok", "error"]
        }
        
        if "paths" in spec_dict:
            for path, path_item in spec_dict["paths"].items():
                for method, operation in path_item.items():
                    if method in ["get", "post", "put", "delete", "patch"]:
                        if "responses" not in operation:
                            operation["responses"] = {}
                        
                        # Update 200 response to include Slack format
                        if "200" in operation["responses"]:
                            operation["responses"]["200"]["content"] = {
                                "application/json": {
                                    "schema": slack_success_schema.copy()
                                }
                            }
                        
                        # Add standard Slack error responses
                        operation["responses"]["400"] = {
                            "description": "Bad Request",
                            "content": {
                                "application/json": {
                                    "schema": slack_error_schema.copy()
                                }
                            }
                        }
    
    def _add_rate_limiting_info(self, spec_dict: Dict[str, Any]):
        """Add Slack rate limiting information"""
        if "info" not in spec_dict:
            spec_dict["info"] = {}
        
        spec_dict["info"]["x-rate-limit"] = {
            "description": "Slack Web API rate limits",
            "limits": {
                "tier1": "1 request per minute",
                "tier2": "20 requests per minute", 
                "tier3": "50 requests per minute",
                "tier4": "100 requests per minute"
            }
        }


class SalesforceSpecProcessor(SpecProcessor):
    """Processor for Salesforce APIs"""
    
    def supports_provider(self, provider: str) -> bool:
        return provider.lower() == "salesforce"
    
    def process_spec(self, spec_dict: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process Salesforce API OpenAPI specifications"""
        # Salesforce often doesn't provide complete OpenAPI specs
        # We may need to generate or enhance them
        
        if not spec_dict or "paths" not in spec_dict:
            # Generate basic Salesforce REST API spec
            spec_dict = self.generate_custom_spec(config)
        
        # Add Salesforce-specific authentication
        self._add_salesforce_auth_schemes(spec_dict)
        
        # Process Salesforce-specific response formats
        self._process_salesforce_responses(spec_dict)
        
        # Handle Salesforce instance URLs
        self._update_server_urls_for_instance(spec_dict, config)
        
        return spec_dict
    
    def generate_custom_spec(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate custom OpenAPI spec for Salesforce"""
        instance = config.get("env_vars", {}).get("instance", "login")
        
        return {
            "openapi": "3.0.3",
            "info": {
                "title": "Salesforce REST API",
                "description": "Salesforce REST API for CRM operations",
                "version": "58.0"
            },
            "servers": [
                {"url": f"https://{instance}.salesforce.com/services/data/v58.0"}
            ],
            "paths": {
                "/sobjects": {
                    "get": {
                        "operationId": "listSObjects",
                        "summary": "List all available SObjects",
                        "responses": {
                            "200": {
                                "description": "List of SObjects",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "sobjects": {
                                                    "type": "array",
                                                    "items": {"$ref": "#/components/schemas/SObject"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/sobjects/{sObjectType}": {
                    "get": {
                        "operationId": "describeSObject",
                        "summary": "Describe an SObject",
                        "parameters": [
                            {
                                "name": "sObjectType",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                                "description": "The SObject type"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "SObject description",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/SObjectDescription"}
                                    }
                                }
                            }
                        }
                    },
                    "post": {
                        "operationId": "createSObject",
                        "summary": "Create a new SObject record",
                        "parameters": [
                            {
                                "name": "sObjectType",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                                "description": "The SObject type"
                            }
                        ],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        },
                        "responses": {
                            "201": {
                                "description": "Record created successfully",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/CreateResponse"}
                                    }
                                }
                            }
                        }
                    }
                },
                "/sobjects/{sObjectType}/{id}": {
                    "get": {
                        "operationId": "getSObject",
                        "summary": "Get an SObject record by ID",
                        "parameters": [
                            {
                                "name": "sObjectType",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            },
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "SObject record",
                                "content": {
                                    "application/json": {
                                        "schema": {"type": "object"}
                                    }
                                }
                            }
                        }
                    },
                    "patch": {
                        "operationId": "updateSObject",
                        "summary": "Update an SObject record",
                        "parameters": [
                            {
                                "name": "sObjectType",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            },
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            }
                        ],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        },
                        "responses": {
                            "204": {"description": "Record updated successfully"}
                        }
                    },
                    "delete": {
                        "operationId": "deleteSObject",
                        "summary": "Delete an SObject record",
                        "parameters": [
                            {
                                "name": "sObjectType",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            },
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {
                            "204": {"description": "Record deleted successfully"}
                        }
                    }
                },
                "/query": {
                    "get": {
                        "operationId": "querySOQL",
                        "summary": "Execute a SOQL query",
                        "parameters": [
                            {
                                "name": "q",
                                "in": "query",
                                "required": True,
                                "schema": {"type": "string"},
                                "description": "SOQL query string"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Query results",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/QueryResponse"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "SObject": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "label": {"type": "string"},
                            "keyPrefix": {"type": "string"},
                            "createable": {"type": "boolean"},
                            "updateable": {"type": "boolean"},
                            "deletable": {"type": "boolean"}
                        }
                    },
                    "SObjectDescription": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "label": {"type": "string"},
                            "fields": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/Field"}
                            }
                        }
                    },
                    "Field": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "label": {"type": "string"},
                            "type": {"type": "string"},
                            "length": {"type": "integer"},
                            "required": {"type": "boolean"}
                        }
                    },
                    "CreateResponse": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "success": {"type": "boolean"},
                            "errors": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "QueryResponse": {
                        "type": "object",
                        "properties": {
                            "totalSize": {"type": "integer"},
                            "done": {"type": "boolean"},
                            "records": {"type": "array", "items": {"type": "object"}},
                            "nextRecordsUrl": {"type": "string"}
                        }
                    }
                },
                "securitySchemes": {}
            }
        }
    
    def _add_salesforce_auth_schemes(self, spec_dict: Dict[str, Any]):
        """Add Salesforce-specific authentication schemes"""
        if "components" not in spec_dict:
            spec_dict["components"] = {}
        
        if "securitySchemes" not in spec_dict["components"]:
            spec_dict["components"]["securitySchemes"] = {}
        
        # Salesforce OAuth2
        spec_dict["components"]["securitySchemes"]["SalesforceOAuth"] = {
            "type": "oauth2",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": "https://login.salesforce.com/services/oauth2/authorize",
                    "tokenUrl": "https://login.salesforce.com/services/oauth2/token",
                    "scopes": {
                        "api": "Access and manage your data (api)",
                        "refresh_token": "Perform requests on your behalf at any time (refresh_token, offline_access)",
                        "full": "Access and manage your data (full)"
                    }
                },
                "password": {
                    "tokenUrl": "https://login.salesforce.com/services/oauth2/token",
                    "scopes": {
                        "api": "Access and manage your data (api)"
                    }
                }
            }
        }
        
        # Session ID authentication
        spec_dict["components"]["securitySchemes"]["SessionId"] = {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Salesforce Session ID (Bearer token)"
        }
    
    def _process_salesforce_responses(self, spec_dict: Dict[str, Any]):
        """Process Salesforce-specific response formats"""
        # Add common Salesforce error responses
        common_errors = {
            "400": {
                "description": "Bad Request - Invalid request",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string"},
                                    "errorCode": {"type": "string"},
                                    "fields": {"type": "array", "items": {"type": "string"}}
                                }
                            }
                        }
                    }
                }
            },
            "401": {
                "description": "Unauthorized - Invalid session",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string"},
                                    "errorCode": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
        
        if "paths" in spec_dict:
            for path, path_item in spec_dict["paths"].items():
                for method, operation in path_item.items():
                    if method in ["get", "post", "put", "delete", "patch"]:
                        if "responses" not in operation:
                            operation["responses"] = {}
                        
                        # Add error responses if not present
                        for status_code, error_response in common_errors.items():
                            if status_code not in operation["responses"]:
                                operation["responses"][status_code] = error_response.copy()
    
    def _update_server_urls_for_instance(self, spec_dict: Dict[str, Any], config: Dict[str, Any]):
        """Update server URLs for Salesforce instance"""
        instance = config.get("env_vars", {}).get("instance")
        if instance and "servers" in spec_dict:
            for server in spec_dict["servers"]:
                if "{instance}" in server["url"]:
                    server["url"] = server["url"].replace("{instance}", instance)


class GenericSpecProcessor(SpecProcessor):
    """Generic processor for any OpenAPI specification"""
    
    def supports_provider(self, provider: str) -> bool:
        return True  # Fallback processor
    
    def process_spec(self, spec_dict: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process any OpenAPI specification with basic enhancements"""
        # Ensure OpenAPI 3.0+ format
        if "swagger" in spec_dict and spec_dict["swagger"] == "2.0":
            spec_dict = self._upgrade_swagger_to_openapi3(spec_dict)
        
        # Add basic authentication if not present
        self._ensure_basic_auth_schemes(spec_dict)
        
        # Add common response formats
        self._add_common_responses(spec_dict)
        
        return spec_dict
    
    def _upgrade_swagger_to_openapi3(self, swagger_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Basic upgrade from Swagger 2.0 to OpenAPI 3.0"""
        openapi_spec = {
            "openapi": "3.0.3",
            "info": swagger_spec.get("info", {}),
            "servers": [],
            "paths": swagger_spec.get("paths", {}),
            "components": {
                "schemas": swagger_spec.get("definitions", {}),
                "securitySchemes": {}
            }
        }
        
        # Convert host and basePath to servers
        if "host" in swagger_spec:
            scheme = swagger_spec.get("schemes", ["https"])[0]
            host = swagger_spec["host"]
            base_path = swagger_spec.get("basePath", "")
            openapi_spec["servers"] = [{"url": f"{scheme}://{host}{base_path}"}]
        
        return openapi_spec
    
    def _ensure_basic_auth_schemes(self, spec_dict: Dict[str, Any]):
        """Ensure basic authentication schemes are present"""
        if "components" not in spec_dict:
            spec_dict["components"] = {}
        
        if "securitySchemes" not in spec_dict["components"]:
            spec_dict["components"]["securitySchemes"] = {}
        
        # Add bearer token auth if no auth schemes present
        if not spec_dict["components"]["securitySchemes"]:
            spec_dict["components"]["securitySchemes"]["BearerAuth"] = {
                "type": "http",
                "scheme": "bearer",
                "description": "Bearer token authentication"
            }
    
    def _add_common_responses(self, spec_dict: Dict[str, Any]):
        """Add common HTTP response codes if missing"""
        common_responses = {
            "400": {"description": "Bad Request"},
            "401": {"description": "Unauthorized"},
            "403": {"description": "Forbidden"},
            "404": {"description": "Not Found"},
            "500": {"description": "Internal Server Error"}
        }
        
        if "paths" in spec_dict:
            for path, path_item in spec_dict["paths"].items():
                for method, operation in path_item.items():
                    if method in ["get", "post", "put", "delete", "patch"]:
                        if "responses" not in operation:
                            operation["responses"] = {}
                        
                        # Add 200 response if missing
                        if "200" not in operation["responses"]:
                            operation["responses"]["200"] = {
                                "description": "Successful response"
                            }


# Processor registry for automatic registration
def get_all_processors() -> List[SpecProcessor]:
    """Get all available spec processors"""
    return [
        GoogleSpecProcessor(),
        AtlassianSpecProcessor(),
        SlackSpecProcessor(),
        SalesforceSpecProcessor(),
        GenericSpecProcessor()  # Always last as fallback
    ]