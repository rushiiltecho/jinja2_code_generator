# Dynamic API Toolset Generator

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
   toolset-cli.py create-config myapi \
     --provider custom \
     --base-url https://api.example.com \
     --spec-url https://api.example.com/openapi.json \
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
