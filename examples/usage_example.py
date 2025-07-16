"""
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
