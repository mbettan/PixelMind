from agents.base_agent import BaseAgent
import json

class PlannerAgent(BaseAgent):
    def __init__(self):
        system_instruction = (
            "You are a Senior Test Engineer. Your goal is to ingest natural language test rules "
            "and visual state to construct a deterministic execution graph. "
            "Output your plan in a structured JSON format containing a list of logical steps. "
            "IMPORTANT: If a goal involves filtering search results (e.g., '1 Bedroom', 'Price < 500k'), "
            "your plan MUST ALWAYS include an explicit 'Apply Filters' or 'Submit Search' step "
            "immediately after the selection step, even if the button is not yet visible in "
            "the initial screenshot. Assume such a button exists on functional search pages.\n"
            "NATIVE WIDGETS: For dropdowns/select lists, use the word 'Select' in the step (e.g., 'Select Option 1 from the dropdown'). "
            "Modern websites often have complex sub-navigation; ensure you navigate to the "
            "specific sub-page (e.g., 'Apartments' or 'Pricing') before attempting searches."
        )
        # Using gemini-3-flash-preview full resource
        super().__init__(model_name="publishers/google/models/gemini-3-flash-preview", system_instruction=system_instruction)

    async def process(self, test_goal: str, visual_context: str = None):
        prompt = f"Test Goal: {test_goal}\n"
        if visual_context:
            prompt += f"Visual Context: {visual_context}\n"
        
        prompt += (
            "\nBased on the goal, generate a step-by-step execution plan. "
            "Each step should have an 'id', 'action', 'description', and 'expected_outcome'."
            "\nOutput ONLY a JSON code block."
        )
        
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={'system_instruction': self.system_instruction}
        )
        return response.text

    def parse_plan(self, plan_text: str):
        try:
            # Simple extractor (could be more robust with regex or structured outputs)
            json_start = plan_text.find("```json")
            if json_start != -1:
                json_end = plan_text.find("```", json_start + 7)
                json_str = plan_text[json_start + 7:json_end].strip()
            else:
                json_str = plan_text.strip()
            
            data = json.loads(json_str)
            
            # Handle list-wrapped dicts
            if isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict):
                data = data[0]

            if isinstance(data, dict):
                # Try common keys for plan lists
                for key in ["execution_plan", "plan", "steps", "test_plan", "test_steps"]:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                return [data] # Fallback to returning the dict as a single step
            return data
        except Exception as e:
            print(f"Error parsing plan: {e}")
            return None
