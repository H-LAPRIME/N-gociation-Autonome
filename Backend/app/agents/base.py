from typing import List, Optional
from agno.agent import Agent

class BaseOmegaAgent:
    def __init__(
        self, 
        name: str, 
        instructions: List[str], 
        tools: Optional[List] = None
    ):
        self.agent = Agent(
            name=name,
            model=None,  # Pending decision
            instructions=instructions,
            tools=tools,
            markdown=True,
            show_tool_calls=True,
            add_datetime_to_instructions=True,
            monitoring=True
        )

    def run(self, message: str):
        return self.agent.run(message)