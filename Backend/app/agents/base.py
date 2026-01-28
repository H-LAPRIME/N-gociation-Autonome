from dotenv import load_dotenv
import os
load_dotenv()  
from typing import List, Optional
from agno.agent import Agent
from agno.models.mistral import MistralChat


class BaseOmegaAgent:
    def __init__(
        self, 
        name: str, 
        instructions: List[str], 
        tools: Optional[List] = None
    ):
        # mistral_api_key = os.getenv("MISTRAL_API_KEY")
        # if not mistral_api_key:
        #     raise ValueError("MISTRAL_API_KEY non défini dans les variables d'environnement.")

        mistral_model = MistralChat(
            id="mistral-large-latest",
            api_key=mistral_api_key # replace with ur key for now :(
        )

        self.agent = Agent(
            name=name,
            model=mistral_model,
            instructions=instructions,
            tools=tools,
            markdown=True
        )

    def run(self, message: str):
        return self.agent.run(message)
