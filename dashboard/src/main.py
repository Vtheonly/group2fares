import streamlit as st
import sys
import os

# Ensure Python path includes 'src'
sys.path.append(os.path.dirname(__file__))

from core.context import TwinContext
from services.asset_server import BackgroundAssetServer
from services.data_loader import DataLoader
from components.viewer import render_viewer
from components.telemetry import render_metrics # (Implementation implied - simple charts)

# Page Config
st.set_page_config(layout="wide", page_title="Factory Twin 5.0", page_icon="🏭")

def main():
    # 1. Start Asset Server (Once)
    BackgroundAssetServer.start()
    
    # 2. Context & Discovery
    ctx = TwinContext()
    projects = ctx.discover_projects()
    
    # 3. Sidebar Navigation
    st.sidebar.title("🏭 Twin Controller")
    
    if not projects:
        st.error("No built factories found. Run the Architect & Builder first.")
        st.stop()
        
    selected_proj = st.sidebar.selectbox(
        "Select Facility", 
        projects, 
        format_func=lambda p: p.name
    )

    # 4. Load Data
    contract = DataLoader.load_contract(selected_proj.contract_path)
    camera_map = DataLoader.load_camera_map(selected_proj.camera_map_path)
    
    machines = contract.get('machines', [])
    machine_names = [m['name'] for m in machines]
    
    # 5. Selection Control
    st.sidebar.markdown("---")
    selected_machine = st.sidebar.selectbox("Inspect Machine", ["Overview"] + machine_names)
    
    # Determine ID for camera snap
    target_id = None
    if selected_machine != "Overview":
        # Find ID from name
        target_obj = next((m for m in machines if m['name'] == selected_machine), None)
        if target_obj:
            target_id = target_obj.get('id', target_obj.get('name'))

    # 6. Main Layout
    col_view, col_data = st.columns([3, 1])
    
    with col_view:
        # Construct Asset URL
        # "scene/factory_complete.glb" is strictly relative to factory_builder/data/<proj>/
        model_url = BackgroundAssetServer.get_url(selected_proj.name, "scene/factory_complete.glb")
        
        st.caption(f"Live View: {selected_proj.name}")
        render_viewer(model_url, camera_map, target_id)

    with col_data:
        st.subheader("Telemetry")
        if selected_machine != "Overview":
            # Show specific data
            telemetry = DataLoader.generate_telemetry(machines).get(target_id, {})
            st.info(f"Machine: {selected_machine}")
            st.metric("Status", telemetry.get("status", "N/A"))
            st.metric("Temperature", f"{telemetry.get('temperature')} °C")
            st.metric("Efficiency", f"{telemetry.get('efficiency')} %")
        else:
            # Aggregate data
            st.metric("Active Machines", len(machines))
            st.metric("Overall Health", "98.2%")

if __name__ == "__main__":
    main()