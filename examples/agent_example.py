"""
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
