#!/usr/bin/env python3
"""
Dynamic API Toolset Generator CLI
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from toolset_configs.generator import CLIInterface


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
