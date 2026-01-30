import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from app.agents.UserProfileAgent import UserProfileAgent

async def test_agent_init():
    try:
        agent = UserProfileAgent()
        print(f"Agent initialized successfully.")
        print(f"Name: {agent.agent.name}")
        print(f"Role: {getattr(agent.agent, 'role', 'Not Set')}")
        print(f"Description: {getattr(agent.agent, 'description', 'Not Set')}")
        print(f"Model ID: {agent.agent.model.id if agent.agent.model else 'No Model'}")
        
    except Exception as e:
        print(f"Failed to initialize agent: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent_init())
