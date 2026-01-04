import streamlit.components.v1 as components
import json
from pathlib import Path

def render_viewer(model_url: str, camera_map: dict, selected_machine_id: str = None, height=600):
    """
    Renders the 3D Viewer IFrame.
    """
    
    # Load HTML Template
    html_path = Path(__file__).parent.parent / "assets" / "viewer.html"
    with open(html_path, "r") as f:
        html_content = f.read()

    # Serialize Data for JS
    cam_json = json.dumps(camera_map)
    
    # We inject the data directly into the HTML before rendering
    # This prevents complex cross-origin messaging issues
    full_html = html_content.replace(
        "/* INJECT_DATA_HERE */",
        (
            f"const MACHINE_CAM_DATA = {cam_json};\n"
            f"const MODEL_URL = '{model_url}';\n"
            f"const TARGET_ID = '{selected_machine_id or ''}';"
        )
    )

    components.html(full_html, height=height)