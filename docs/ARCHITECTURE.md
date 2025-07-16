# Architecture Documentation

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
