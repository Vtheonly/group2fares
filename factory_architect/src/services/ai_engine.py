import json
import google.generativeai as genai
from loguru import logger
from src.core.config import settings
from src.models.schema import FactoryInput, LayoutSchema

class LayoutIntelligence:
    def __init__(self):
        # Configure Google GenAI
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        # DEBUG: List available models
        logger.info("Listing available models...")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                logger.info(f"Available: {m.name}")

        self.model = genai.GenerativeModel(settings.MODEL_NAME)

    def compute_layout(self, data: FactoryInput) -> LayoutSchema:
        logger.info(f"Computing layout for '{data.project_name}' using Google SDK ({settings.MODEL_NAME})...")

        system_instruction = """
        You are a Factory Layout Physics Engine.
        You will receive a list of Machines (Nodes), Relationships (Edges), and a Process Description.

        YOUR TASK:
        Embed this topological graph into a 2D geometric space (Unit: Millimeters).

        GEOMETRIC RULES:
        1.  **Snake/Cellular Flow**: Do NOT place machines in a single infinite straight line.
        2.  **Staggering**: Place a maximum of 3 machines colinearly. Then, turn the flow 90 or 180 degrees.
        3.  **Parallel Branches**: If the input graph splits (one node to multiple), arrange them visually parallel.
        4.  **Spacing**: Minimum 1500mm clearance between machines.
        5.  **Coordinates**: Origin is (0,0). X is Width, Y is Height.
        6.  **Orientation**: Rotate machines (0, 90, 180, 270) to align input/output ports logically along the flow path.

        CONTEXTUAL UNDERSTANDING:
        Read the 'process_description'. If it mentions "compact", "U-shape", or specific constraints (e.g., "drying oven is long"), prioritize those spatial requirements.

        OUTPUT REQUIREMENTS:
        - Return ONLY valid JSON.
        - **DO NOT WRAP the output in a root key like 'layout' or 'data'. Return the object directly.**
        - **EVERY Machine object MUST have: 'dimensions' (width, length), 'position' (x, y), and 'rotation' (float).**
        - **'flow_connections' is REQUIRED and must match the input relationships.**
        - Calculate 'path_points' for every relationship defined in the input. 
        - The path should be a logical polyline (Manhattan routing preferred: 90-degree turns) connecting the center of source to center of destination.

        EXAMPLE OUTPUT FORMAT:
        {
          "room_width": 50000.0,
          "room_height": 30000.0,
          "machines": [
            {
               "id": "m1", "name": "Machine A", 
               "dimensions": {"length": 2000.0, "width": 1000.0},
               "position": {"x": 5000.0, "y": 5000.0},
               "rotation": 0.0
            }
          ],
          "flow_connections": [
            {
               "from_machine_id": "m1", "to_machine_id": "m2",
               "connection_type": "conveyor",
               "path_points": [{"x": 6000.0, "y": 5500.0}, {"x": 8000.0, "y": 5500.0}]
            }
          ]
        }
        """

        # We explicitly dump the input data into the user prompt
        user_content = f"""
        PROJECT: {data.project_name}
        DESCRIPTION: {data.process_description}
        
        MACHINES:
        {json.dumps([m.model_dump() for m in data.machines])}
        
        RELATIONSHIPS (Must be preserved):
        {json.dumps([r.model_dump() for r in data.relationships])}
        """

        try:
            logger.debug("Sending payload to Google AI...")
            
            # Combine system and user content because GenAI Python SDK handles system instructions differently in beta,
            # but concatenating them is robust for the stable SDK.
            full_prompt = f"{system_instruction}\n\n---\n\n{user_content}"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    candidate_count=1,
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )
            
            content = response.text
            
            # Robust Cleaning (even if MIME type is set, sometimes markdown leaks)
            if "```" in content:
                try:
                    content = content.split("```", 1)[1]
                    if "```" in content:
                        content = content.rsplit("```", 1)[0]
                except IndexError:
                    pass
                if content.strip().startswith("json"):
                    content = content.strip()[4:]

            content = content.strip()
            
            # Parse JSON first to handle wrappers
            try:
                raw_data = json.loads(content)
            except json.JSONDecodeError:
                # Fallback extraction
                if "{" in content:
                    content = content[content.find("{"):content.rfind("}")+1]
                    raw_data = json.loads(content)
                else:
                    raise

            # Unwrap if necessary
            if "layout" in raw_data and isinstance(raw_data["layout"], dict) and "machines" in raw_data["layout"]:
                raw_data = raw_data["layout"]
            elif "data" in raw_data and isinstance(raw_data["data"], dict) and "machines" in raw_data["data"]:
                raw_data = raw_data["data"]

            # Validation
            return LayoutSchema(**raw_data)

        except Exception as e:
            logger.error(f"AI Logic Failure: {e}")
            # Log response feedback if available
            try:
                if 'response' in locals() and response.prompt_feedback:
                    logger.error(f"Feedback: {response.prompt_feedback}")
            except:
                pass
                
            raise

class PlanerIntelligence:
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(settings.MODEL_NAME)

    def generate_input_schema(self, project_notes: dict) -> FactoryInput:
        logger.info("Planer Agent is analyzing project notes to extract a production line...")

        system_instruction = """
        You are a Factory Process Architect.
        Your goal is to analyze a complex industrial project document and extract ONE specific, high-priority production line.

        TASK:
        1. Identify a primary production line mentioned in the notes (e.g., "SPC Flooring Line", "Glass Lamination", etc.).
        2. Break it down into a sequence of machines (approx 5-10 machines).
        3. Assign realistic dimensions (Length/Width in mm) to each machine.
        4. Define the logical connections (Relationships) between them.
        5. Write a concise 'process_description' outlining the flow.

        OUTPUT REQUIREMENTS:
        - Return ONLY valid JSON matching the 'FactoryInput' schema.
        - **DO NOT WRAP the output.**
        - Be precise with machine IDs (e.g., 'm_mixer', 'm_extruder').

        SCHEMA STRUCTURE:
        {
          "project_name": "String",
          "process_description": "String",
          "machines": [
            { "id": "m1", "name": "Name", "dimensions": {"length": 5000, "width": 2000} }
          ],
          "relationships": [
            { "from_id": "m1", "to_id": "m2", "type": "conveyor|pipe|etc" }
          ]
        }
        """

        try:
            prompt = f"{system_instruction}\n\nPROJECT DATA:\n{json.dumps(project_notes)}"
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )
            
            content = response.text.strip()
            
            # Cleaning
            if "```" in content:
                content = content.split("```", 1)[1]
                if "```" in content:
                    content = content.rsplit("```", 1)[0]
                if content.strip().startswith("json"):
                    content = content.strip()[4:]

            raw_data = json.loads(content.strip())
            
            # Validate against Pydantic
            return FactoryInput(**raw_data)

        except Exception as e:
            logger.error(f"Planer Logic Failure: {e}")
            raise
