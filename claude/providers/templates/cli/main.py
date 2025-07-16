# {# CLI Tool Template: toolset_configs/templates/cli/main.py.j2 #}
#!/usr/bin/env python3
"""
Dynamic API Toolset Generator CLI
=================================

Command-line interface for managing and generating API toolsets
"""

import argparse
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the generator (assuming it's in the same package)
try:
    from toolset_configs.generator import ToolsetGenerator, CLIInterface
except ImportError:
    # Fallback for standalone usage
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from toolset_configs.generator import ToolsetGenerator, CLIInterface


def create_config_command(args):
    """Create a new API configuration"""
    config_data = {
        'name': args.name,
        'provider': args.provider,
        'base_url': args.base_url,
        'spec_url': args.spec_url,
        'auth_type': args.auth_type,
        'scopes': {},
        'auth_endpoints': {},
        'env_vars': {},
        'custom_headers': {},
        'metadata': {}
    }
    
    # Add optional fields if provided
    if args.scopes:
        config_data['scopes'] = dict(scope.split('=') for scope in args.scopes)
    
    if args.env_vars:
        config_data['env_vars'] = dict(var.split('=') for var in args.env_vars)
    
    # Create the config file
    cli = CLIInterface(Path(args.config_dir))
    config_dir = cli.generator.config_manager.providers_dir / args.provider
    config_dir.mkdir(parents=True, exist_ok=True)
    
    config_file = config_dir / f"{args.api_name}.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False)
    
    print(f"✅ Created configuration: {config_file}")


def validate_command(args):
    """Validate configurations and generated toolsets"""
    cli = CLIInterface(Path(args.config_dir))
    
    print("🔍 Validating configurations...")
    
    # Load all configurations
    all_configs = cli.generator.config_manager.load_all_configs()
    
    validation_results = {
        'providers': len(all_configs),
        'total_configs': sum(len(configs) for configs in all_configs.values()),
        'valid_configs': 0,
        'invalid_configs': [],
        'missing_env_vars': [],
        'spec_url_issues': []
    }
    
    for provider, configs in all_configs.items():
        print(f"\n📋 Validating {provider} provider:")
        
        for config in configs:
            api_name = config.name.lower().replace(' ', '_')
            print(f"  - {api_name}...", end=' ')
            
            try:
                # Validate required fields
                required_fields = ['name', 'base_url', 'spec_url', 'auth_type']
                missing_fields = [field for field in required_fields 
                                if not getattr(config, field, None)]
                
                if missing_fields:
                    print(f"❌ Missing fields: {missing_fields}")
                    validation_results['invalid_configs'].append({
                        'provider': provider,
                        'api': api_name,
                        'issues': f"Missing fields: {missing_fields}"
                    })
                    continue
                
                # Check environment variables
                missing_env_vars = []
                for env_var in config.env_vars.values():
                    import os
                    if not os.getenv(env_var):
                        missing_env_vars.append(env_var)
                
                if missing_env_vars:
                    validation_results['missing_env_vars'].append({
                        'provider': provider,
                        'api': api_name,
                        'missing_vars': missing_env_vars
                    })
                
                # Test spec URL accessibility (basic check)
                if config.spec_url and not config.spec_url.startswith('custom://'):
                    try:
                        import requests
                        response = requests.head(config.spec_url, timeout=10)
                        if response.status_code >= 400:
                            validation_results['spec_url_issues'].append({
                                'provider': provider,
                                'api': api_name,
                                'url': config.spec_url,
                                'status': response.status_code
                            })
                    except Exception as e:
                        validation_results['spec_url_issues'].append({
                            'provider': provider,
                            'api': api_name,
                            'url': config.spec_url,
                            'error': str(e)
                        })
                
                validation_results['valid_configs'] += 1
                print("✅")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                validation_results['invalid_configs'].append({
                    'provider': provider,
                    'api': api_name,
                    'issues': str(e)
                })
    
    # Print summary
    print(f"\n📊 Validation Summary:")
    print(f"  Total providers: {validation_results['providers']}")
    print(f"  Total configurations: {validation_results['total_configs']}")
    print(f"  Valid configurations: {validation_results['valid_configs']}")
    print(f"  Invalid configurations: {len(validation_results['invalid_configs'])}")
    print(f"  Missing environment variables: {len(validation_results['missing_env_vars'])}")
    print(f"  Spec URL issues: {len(validation_results['spec_url_issues'])}")
    
    if args.detailed:
        if validation_results['invalid_configs']:
            print(f"\n❌ Invalid configurations:")
            for item in validation_results['invalid_configs']:
                print(f"  - {item['provider']}/{item['api']}: {item['issues']}")
        
        if validation_results['missing_env_vars']:
            print(f"\n⚠️  Missing environment variables:")
            for item in validation_results['missing_env_vars']:
                print(f"  - {item['provider']}/{item['api']}: {', '.join(item['missing_vars'])}")
        
        if validation_results['spec_url_issues']:
            print(f"\n🌐 Spec URL issues:")
            for item in validation_results['spec_url_issues']:
                status = item.get('status', item.get('error', 'Unknown'))
                print(f"  - {item['provider']}/{item['api']}: {item['url']} ({status})")
    
    # Save validation report if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(validation_results, f, indent=2)
        print(f"\n💾 Validation report saved to: {args.output}")


def test_command(args):
    """Test a specific toolset"""
    cli = CLIInterface(Path(args.config_dir))
    
    print(f"🧪 Testing {args.provider}/{args.api} toolset...")
    
    try:
        # Generate the toolset if it doesn't exist
        output_dir = Path(args.output_dir)
        toolset_file = output_dir / f"{args.api}_toolset.py"
        
        if not toolset_file.exists():
            print("  📦 Generating toolset...")
            cli.generator.generate_toolset(args.provider, args.api, output_dir)
        
        # Try to import and instantiate the toolset
        print("  📥 Importing toolset...")
        sys.path.insert(0, str(output_dir))
        
        module_name = f"{args.api}_toolset"
        class_name = ''.join(word.capitalize() for word in args.api.split('_')) + 'Toolset'
        
        module = __import__(module_name)
        toolset_class = getattr(module, class_name)
        
        print("  🔧 Creating toolset instance...")
        # Create with minimal configuration for testing
        toolset = toolset_class()
        
        print("  ✅ Validating configuration...")
        issues = toolset.validate_configuration()
        
        if issues:
            print("  ⚠️  Configuration issues found:")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print("  ✅ Configuration is valid!")
        
        print("  📋 Getting API info...")
        api_info = toolset.get_api_info()
        print(f"    Name: {api_info['name']}")
        print(f"    Provider: {api_info['provider']}")
        print(f"    Auth Type: {api_info['auth_type']}")
        print(f"    Base URL: {api_info['base_url']}")
        
        if not issues:
            print("  🔨 Testing tool generation...")
            try:
                tools = toolset.get_tools()
                print(f"    Generated {len(tools)} tools")
                
                if args.list_tools and tools:
                    print("    Available tools:")
                    for i, tool in enumerate(tools[:5]):  # Show first 5 tools
                        tool_name = getattr(tool, 'name', f'Tool_{i}')
                        print(f"      - {tool_name}")
                    if len(tools) > 5:
                        print(f"      ... and {len(tools) - 5} more tools")
                        
            except Exception as e:
                print(f"    ❌ Tool generation failed: {e}")
        
        print(f"✅ Test completed for {args.provider}/{args.api}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)


def info_command(args):
    """Show information about available providers and APIs"""
    cli = CLIInterface(Path(args.config_dir))
    
    if args.provider:
        # Show specific provider info
        configs = cli.generator.config_manager.load_provider_configs(args.provider)
        if not configs:
            print(f"❌ Provider '{args.provider}' not found or has no configurations")
            return
        
        print(f"📋 Provider: {args.provider}")
        print(f"   APIs: {len(configs)}")
        print()
        
        for config in configs:
            api_name = config.name.lower().replace(' ', '_')
            print(f"🔧 {api_name}")
            print(f"   Name: {config.name}")
            print(f"   Base URL: {config.base_url}")
            print(f"   Auth Type: {config.auth_type}")
            print(f"   Scopes: {', '.join(config.scopes.keys()) if config.scopes else 'None'}")
            if config.metadata:
                if 'documentation' in config.metadata:
                    print(f"   Documentation: {config.metadata['documentation']}")
                if 'rate_limits' in config.metadata:
                    print(f"   Rate Limits: {config.metadata['rate_limits']}")
            print()
    else:
        # Show all providers
        all_configs = cli.generator.config_manager.load_all_configs()
        
        print("📋 Available Providers and APIs:")
        print(f"   Total Providers: {len(all_configs)}")
        print(f"   Total APIs: {sum(len(configs) for configs in all_configs.values())}")
        print()
        
        for provider, configs in all_configs.items():
            print(f"🏢 {provider} ({len(configs)} APIs)")
            for config in configs:
                api_name = config.name.lower().replace(' ', '_')
                auth_type = config.auth_type
                print(f"   - {api_name} ({auth_type})")
            print()


def clean_command(args):
    """Clean generated files"""
    output_dir = Path(args.output_dir)
    
    if not output_dir.exists():
        print(f"❌ Output directory does not exist: {output_dir}")
        return
    
    print(f"🧹 Cleaning generated files in {output_dir}...")
    
    # Remove generated toolset files
    removed_count = 0
    for file_path in output_dir.glob("*_toolset.py"):
        file_path.unlink()
        removed_count += 1
        print(f"  ✅ Removed {file_path.name}")
    
    # Remove registry file
    registry_file = output_dir / "__init__.py"
    if registry_file.exists():
        registry_file.unlink()
        removed_count += 1
        print(f"  ✅ Removed {registry_file.name}")
    
    # Remove __pycache__ directories
    for pycache_dir in output_dir.glob("**/__pycache__"):
        import shutil
        shutil.rmtree(pycache_dir)
        print(f"  ✅ Removed {pycache_dir}")
    
    print(f"🎉 Cleaned {removed_count} files")


def export_command(args):
    """Export configurations or generated code"""
    cli = CLIInterface(Path(args.config_dir))
    
    if args.format == 'json':
        # Export all configurations as JSON
        all_configs = cli.generator.config_manager.load_all_configs()
        
        export_data = {}
        for provider, configs in all_configs.items():
            export_data[provider] = []
            for config in configs:
                config_dict = {
                    'name': config.name,
                    'provider': config.provider,
                    'base_url': config.base_url,
                    'spec_url': config.spec_url,
                    'auth_type': config.auth_type,
                    'scopes': config.scopes,
                    'auth_endpoints': config.auth_endpoints,
                    'env_vars': config.env_vars,
                    'custom_headers': config.custom_headers,
                    'server_url_template': config.server_url_template,
                    'custom_processors': config.custom_processors,
                    'metadata': config.metadata
                }
                export_data[provider].append(config_dict)
        
        with open(args.output, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"📄 Exported configurations to {args.output}")
    
    elif args.format == 'env':
        # Export environment variables template
        all_configs = cli.generator.config_manager.load_all_configs()
        
        env_vars = set()
        for provider, configs in all_configs.items():
            for config in configs:
                env_vars.update(config.env_vars.values())
        
        with open(args.output, 'w') as f:
            f.write("# Environment Variables for Dynamic API Toolset Generator\n")
            f.write("# Copy this file to .env and fill in your actual values\n\n")
            
            for env_var in sorted(env_vars):
                f.write(f"{env_var}=your_{env_var.lower()}_here\n")
        
        print(f"📄 Exported environment variables template to {args.output}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Dynamic API Toolset Generator CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize a new project
  %(prog)s init

  # List all available providers and APIs  
  %(prog)s info

  # Generate toolsets for Google provider
  %(prog)s generate --provider google

  # Create a new API configuration
  %(prog)s create-config myapi --provider custom --base-url https://api.example.com --spec-url https://api.example.com/openapi.json --auth-type bearer

  # Validate all configurations
  %(prog)s validate --detailed

  # Test a specific toolset
  %(prog)s test google calendar

  # Export configurations as JSON
  %(prog)s export --format json --output configs.json
        """
    )
    
    parser.add_argument("--config-dir", default="toolset_configs",
                       help="Configuration directory (default: toolset_configs)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize new project")
    init_parser.add_argument("--force", action="store_true",
                            help="Overwrite existing configuration")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show provider and API information")
    info_parser.add_argument("--provider", help="Show info for specific provider")
    
    # List command (alias for info)
    subparsers.add_parser("list", help="List available providers and APIs")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate toolsets")
    gen_parser.add_argument("--provider", help="Specific provider to generate")
    gen_parser.add_argument("--api", help="Specific API to generate")
    gen_parser.add_argument("--output", default="generated_toolsets",
                           help="Output directory (default: generated_toolsets)")
    
    # Create config command
    config_parser = subparsers.add_parser("create-config", help="Create new API configuration")
    config_parser.add_argument("api_name", help="API name (used for filename)")
    config_parser.add_argument("--name", required=True, help="Display name for the API")
    config_parser.add_argument("--provider", required=True, help="Provider name")
    config_parser.add_argument("--base-url", required=True, help="Base URL for the API")
    config_parser.add_argument("--spec-url", required=True, help="OpenAPI specification URL")
    config_parser.add_argument("--auth-type", required=True, 
                              choices=["oauth2", "bearer", "api_key", "basic"],
                              help="Authentication type")
    config_parser.add_argument("--scopes", nargs="*", 
                              help="OAuth scopes (format: name=scope_url)")
    config_parser.add_argument("--env-vars", nargs="*",
                              help="Environment variables (format: var_name=ENV_VAR_NAME)")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate configurations")
    validate_parser.add_argument("--detailed", action="store_true",
                                help="Show detailed validation results")
    validate_parser.add_argument("--output", help="Save validation report to file")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test a specific toolset")
    test_parser.add_argument("provider", help="Provider name")
    test_parser.add_argument("api", help="API name")
    test_parser.add_argument("--output-dir", default="generated_toolsets",
                            help="Output directory for generated toolsets")
    test_parser.add_argument("--list-tools", action="store_true",
                            help="List available tools after generation")
    
    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean generated files")
    clean_parser.add_argument("--output-dir", default="generated_toolsets",
                             help="Output directory to clean")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export configurations or code")
    export_parser.add_argument("--format", choices=["json", "env"], required=True,
                              help="Export format")
    export_parser.add_argument("--output", required=True, help="Output file")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle commands
    try:
        if args.command == "init":
            cli = CLIInterface(Path(args.config_dir))
            cli.init_project(getattr(args, 'force', False))
        
        elif args.command in ["info", "list"]:
            info_command(args)
        
        elif args.command == "generate":
            cli = CLIInterface(Path(args.config_dir))
            cli.generate(args.provider, args.api, args.output)
        
        elif args.command == "create-config":
            create_config_command(args)
        
        elif args.command == "validate":
            validate_command(args)
        
        elif args.command == "test":
            test_command(args)
        
        elif args.command == "clean":
            clean_command(args)
        
        elif args.command == "export":
            export_command(args)
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Command failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()