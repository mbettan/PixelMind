from agents.base_agent import BaseAgent
import json
import base64
from google.genai.types import Part

class ActorAgent(BaseAgent):
    def __init__(self):
        system_instruction = (
            "You are the Actor Agent of an autonomous web testing framework. Your job "
            "is to translate a single logical step into precise actions on a 0-1000 "
            "normalized coordinate grid (0,0 = top-left; 1000,1000 = bottom-right). "
            "You receive a screenshot and ONE step to execute.\n\n"
            "COORDINATE SYSTEM:\n"
            "- x: 0 = left edge, 1000 = right edge\n"
            "- y: 0 = top edge, 1000 = bottom edge\n"
            "- Be precise — aim for the CENTER of the target element.\n\n"
            "OUTPUT FORMAT — return a JSON object:\n"
            "{\n"
            "  \"actions\": [\n"
            "    {\n"
            "      \"type\": \"click|type|select|scroll|press_key|wait\",\n"
            "      \"x\": 500,\n"
            "      \"y\": 300,\n"
            "      \"text\": \"optional text for type/select action\",\n"
            "      \"key\": \"optional key name for press_key\",\n"
            "      \"direction\": \"up|down (for scroll)\",\n"
            "      \"amount\": 300,\n"
            "      \"confidence\": 0.95,\n"
            "      \"element_description\": \"what you identified as the target\"\n"
            "    }\n"
            "  ],\n"
            "  \"reasoning\": \"Explain what you see and why you chose these coordinates.\"\n"
            "}\n\n"
            "RULES:\n"
            "1. Output a list of one or more 'actions' to complete the step.\n"
            "2. If an element is already in the desired state, skip the action.\n"
            "3. Use 'select' for native HTML dropdowns by providing coordinates of the dropdown and the 'text' of the option.\n"
            "4. For wait, do NOT provide x/y. It means wait for visual stability.\n"
        )
        # Using gemini-3-flash-preview full resource
        super().__init__(model_name="publishers/google/models/gemini-3-flash-preview", system_instruction=system_instruction)

    async def process(self, step: dict, screenshot: bytes, context: str = ""):
        prompt_text = f"Current Step: {json.dumps(step)}\n"
        if context:
            prompt_text += f"Context: {context}\n"
        prompt_text += (
            "\nBased on the screenshot, determine the sequence of actions to accomplish this step. "
            "Target the CENTER of elements. Output ONLY the JSON block."
        )

        contents = [
            Part.from_text(text=prompt_text),
            Part.from_bytes(data=screenshot, mime_type="image/png")
        ]
        
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=contents,
            config={'system_instruction': self.system_instruction}
        )
        return response.text

    def parse_action(self, action_text: str):
        try:
            # Clean up potential markdown formatting
            cleaned = action_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except Exception as e:
            print(f"Error parsing actor action: {e}")
            return None
