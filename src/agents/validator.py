from agents.base_agent import BaseAgent
import json
from google.genai.types import Part

class ValidatorAgent(BaseAgent):
    def __init__(self):
        system_instruction = (
            "You are the Validator Agent of an autonomous web testing framework.\n\n"
            "Your job:\n"
            "1. You receive a BEFORE screenshot, an AFTER screenshot, the action taken, "
            "and the expected outcome.\n"
            "2. Determine if the expected outcome was achieved.\n"
            "3. Check for visual anomalies (wrong images, mismatched content, UI errors).\n\n"
            "WRONG IMAGE DETECTION: If a text label describes a product (e.g., 'Red Leather Handbag') "
            "but the image shows something different (e.g., 'blue shoes'), flag this as a 'wrong_image' issue.\n\n"
            "OUTPUT FORMAT — return a JSON object:\n"
            "{\n"
            "  \"passed\": true|false,\n"
            "  \"confidence\": 0.0-1.0,\n"
            "  \"actual_outcome\": \"What actually happened visually\",\n"
            "  \"issues\": [\n"
            "    {\n"
            "      \"type\": \"routing_failure|wrong_image|ui_error|content_mismatch|unexpected_state\",\n"
            "      \"severity\": \"blocker|critical|major|minor\",\n"
            "      \"description\": \"Detailed description of the issue\",\n"
            "      \"evidence\": \"Visual evidence summary\"\n"
            "    }\n"
            "  ],\n"
            "  \"page_state_summary\": \"Brief description of current page state\",\n"
            "  \"reasoning\": \"Explain your validation logic\"\n"
            "}\n\n"
            "RULES:\n"
            "- Be strict — only mark passed=true if outcome clearly matches.\n"
            "- If the AFTER state matches 'Expected Outcome', PASS even if identical to BEFORE.\n"
            "- A confidence below 0.5 should result in passed=false.\n"
        )
        super().__init__(model_name="publishers/google/models/gemini-3-flash-preview", system_instruction=system_instruction)

    async def process(self, action_taken: str, expected_outcome: str, before_screenshot: bytes, after_screenshot: bytes):
        prompt_text = (
            f"VALIDATION TASK:\n"
            f"- Action taken: {action_taken}\n"
            f"- Expected outcome: {expected_outcome}\n\n"
            "Two screenshots are attached: 1. BEFORE, 2. AFTER.\n"
            "Determine if success was achieved. Output ONLY the JSON block."
        )

        contents = [
            Part.from_text(text=prompt_text),
            Part.from_bytes(data=before_screenshot, mime_type="image/png"),
            Part.from_bytes(data=after_screenshot, mime_type="image/png")
        ]
        
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=contents,
            config={'system_instruction': self.system_instruction, 'response_mime_type': 'application/json'}
        )
        return response.text

    async def validate_final_goal(self, goal: str, final_screenshot: bytes, scenario_context: str = "", step_results: list[dict] = None):
        """
        Final verification — did we achieve the overall test goal?
        Uses step history for deeper context.
        """
        history_summary = ""
        if step_results:
            history_summary = "\n".join([
                f"  - Step {r['step_number']}: {r['description']} -> {'PASS' if r['passed'] else 'FAIL'}"
                for r in step_results
            ])

        prompt_text = (
            f"FINAL GOAL VALIDATION:\n"
            f"- Test Goal: {goal}\n"
            f"- Context: {scenario_context}\n"
        )
        if history_summary:
            prompt_text += f"- Execution History:\n{history_summary}\n"
            
        prompt_text += (
            "\nThe attached screenshot shows the final state of the page.\n"
            "Determine if the overall goal was achieved. Output ONLY the JSON block."
        )

        contents = [
            Part.from_text(text=prompt_text),
            Part.from_bytes(data=final_screenshot, mime_type="image/png")
        ]
        
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=contents,
            config={'system_instruction': self.system_instruction, 'response_mime_type': 'application/json'}
        )
        return response.text

    def parse_validation(self, validation_text: str):
        try:
            # Handle potential markdown fencing
            cleaned = validation_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except Exception:
            return None
