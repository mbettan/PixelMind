from google import genai
import os
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, model_name: str, system_instruction: str = None):
        # Using project ID from environment if available, fallback to the one found in logs
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
        print(f"[Debug] Initializing GenAI Client - Project: {project_id}, Location: {location}, Model: {model_name}")
        
        # New google-genai Client
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location
        )
        self.model_name = model_name
        self.system_instruction = system_instruction

    @abstractmethod
    async def process(self, *args, **kwargs):
        pass

    async def close(self):
        """Properly close the GenAI client."""
        if hasattr(self, 'client') and hasattr(self.client, 'aio'):
            # Close the async client
            await self.client.aio.aclose()
