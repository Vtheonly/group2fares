import streamlit as st
import streamlit.components.v1 as components
import json
import os
import time
import random
import re
from pathlib import Path
import plotly.graph_objects as go

# ==========================================
# 1. ROBUST PATH CONFIG
# ==========================================
st.set_page_config(layout="wide", page_title="Factory 5.0 Twin (Discovery)")

# The Asset Server is mandatory for the viewer
ASSET_SERVER_URL = "http://localhost:8000"

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    h1, h2, h3 { color: #00d2ff !important; font-family: 'Segoe UI', sans-serif; }
    div[data-testid="stMetricValue"] { color: #00ff88; font-family: 'Courier New'; }
    .stSidebar { background-color: #161b22; }
</style>
""", unsafe_allow_html=True)

# Communication Bridge Relay Logic
# This script runs in the MAIN window and relays messages from Streamlit components to the Viewer iframe.
# It bypasses typical cross-origin restriction issues for direct script-to-iframe calls.
# Communication Bridge Relay Logic
# Robust Broadcast-Forward Architecture
st.markdown("""
<script>
    window.addEventListener('message', function(e) {
        // Filter for our specific event types to avoid noise
        if (e.data && e.data.type && (e.data.type === 'FOCUS' || e.data.type === 'SYNC_DATA')) {
            console.log("Global Relay: Broadcasting", e.data.type);
            
            // Broadcast to ALL Streamlit component iframes
            // We cannot inspect them due to cross-origin rules, so we send to all.
            const frames = document.getElementsByTagName('iframe');
            for (let i = 0; i < frames.length; i++) {
                try {
                    frames[i].contentWindow.postMessage(e.data, '*');
                } catch (err) {
                    // Ignore errors for cross-origin frames that might reject it
                }
            }
        }
    });
</script>
""", unsafe_allow_html=True)
# ==========================================
# 2. GLOBAL DISCOVERY SYSTEM
# ==========================================
@st.cache_data(ttl=60)
def discover_all_projects():
    """
    Scans the workspace recursively for debug_layout.json files
    and attempts to find their corresponding GLB files.
    """
    found_projects = []
    workspace_root = Path(os.getcwd())
    
    # 1. Find all debug_layout.json files
    for layout_path in workspace_root.rglob("debug_layout.json"):
        if ".git" in layout_path.parts or "twin_venv" in layout_path.parts:
            continue
            
        project_name = layout_path.parent.name
        # Sometimes project_name is "output", try one level up
        if project_name == "output":
            project_name = layout_path.parent.parent.name
            
        # 2. Try to find the associated GLB
        glb_path = None
        
        # Strategy A: Look in the metadata's own scene/ folder
        scene_dir = layout_path.parent / "scene"
        if scene_dir.exists():
            glbs = list(scene_dir.glob("*_complete.glb")) + list(scene_dir.glob("*.glb"))
            if glbs: glb_path = glbs[0]
            
        # Strategy B: Look in factory_builder/output (User-specified path)
        if not glb_path:
            builder_out = workspace_root / "factory_builder" / "output"
            if builder_out.exists():
                # Try to match by project name prefix
                pattern = f"{project_name}*_scene_gray.glb"
                matches = list(builder_out.glob(pattern)) or list(builder_out.glob("*.glb"))
                if matches: glb_path = matches[0]

        if glb_path:
            found_projects.append({
                "name": project_name,
                "layout": layout_path,
                "glb": glb_path,
                "mtime": layout_path.stat().st_mtime
            })
            
    # Sort by modification time
    found_projects.sort(key=lambda x: x['mtime'], reverse=True)
    return found_projects

# ==========================================
# 3. SEMANTIC METRIC GENERATOR
# ==========================================
def generate_metrics_for_machine(machine_name):
    name_lower = machine_name.lower()
    metrics = {}
    
    # Thermal
    if any(x in name_lower for x in ['oven', 'dry', 'cool', 'heat', 'furnace', 'autoclave', 'temper']):
        metrics["Temperature"] = {"unit": "°C", "target": 120 if 'heat' in name_lower else 15, "range": [0, 200], "color": "#ffaa00"}
        metrics["Air Flow"] = {"unit": "m³/h", "target": 1500, "range": [0, 2000], "color": "#00d2ff"}
    # Kinetic
    if any(x in name_lower for x in ['mix', 'extru', 'roll', 'conveyor', 'spin', 'centrifuge']):
        metrics["Motor Speed"] = {"unit": "RPM", "target": 1450, "range": [0, 3000], "color": "#00ff88"}
        metrics["Torque"] = {"unit": "Nm", "target": 450, "range": [0, 800], "color": "#ff0055"}
    # Pressure
    if any(x in name_lower for x in ['press', 'vac', 'lamination', 'pump']):
        metrics["Pressure"] = {"unit": "Bar", "target": 8.5, "range": [0, 15], "color": "#ff0055"}

    if not metrics:
        metrics["Utilization"] = {"unit": "%", "target": 85, "range": [0, 100], "color": "#00d2ff"}
    return metrics

# ==========================================
# 4. SIMULATION & HISTORY
# ==========================================
if 'history' not in st.session_state:
    st.session_state.history = {}

def generate_snapshot(machines):
    snapshot = {}
    for m in machines:
        node_id = m.get('id', m['name'])
        cfg = generate_metrics_for_machine(m['name'])
        
        # Current Values
        vals = {}
        for k, c in cfg.items():
            noise = (c['range'][1] - c['range'][0]) * 0.05
            v = round(c['target'] + random.uniform(-noise, noise), 2)
            vals[k] = v
            
            # Update History
            hist_key = f"{node_id}_{k}"
            if hist_key not in st.session_state.history:
                st.session_state.history[hist_key] = []
            st.session_state.history[hist_key].append(v)
            if len(st.session_state.history[hist_key]) > 30:
                st.session_state.history[hist_key].pop(0)

        snapshot[node_id] = {
            "metrics": vals, 
            "status": "RUNNING", 
            "health": round(random.uniform(94, 100), 1), 
            "display_name": m['name']
        }
    return snapshot

# ==========================================
# 5. DASHBOARD UI
# ==========================================
st.sidebar.header("🏭 Global Twin Discovery")
projects = discover_all_projects()

if not projects:
    st.error("No valid project/GLB pairs discovered in workspace.")
    if st.sidebar.button("Retry Scan"): st.rerun()
    st.stop()

selected_name = st.sidebar.selectbox("Active Simulation Stamp", [p['name'] for p in projects])
proj = next(p for p in projects if p['name'] == selected_name)

# Ingest Metadata
with open(proj['layout'], 'r') as f: layout_data = json.load(f)
machines = layout_data.get('machines', [])
machine_map = {m.get('id', m['name']): m for m in machines}

st.sidebar.info(f"Metadata: {proj['layout'].relative_to(os.getcwd())}")
st.sidebar.info(f"Geometry: {proj['glb'].relative_to(os.getcwd())}")
# Viewer Integration
col_viewer, col_data = st.columns([3, 2])

with col_viewer:
    # URL encoded to be absolute from current working directory
    rel_glb = proj['glb'].relative_to(os.getcwd())
    model_url = f"{ASSET_SERVER_URL}/{rel_glb}"
    viewer_url = f"{ASSET_SERVER_URL}/static/viewer.html?model_url={model_url}"
    
    components.html(
        f"""
        <iframe 
            id="viewer_iframe"
            src="{viewer_url}" 
            width="100%" height="700px" 
            title="factory_viewer"
            style="border:none; border-radius:12px; background:#000;"
            allow="accelerometer; autoplay; encrypted-media; gyroscope;"
        ></iframe>
        <script>
            // Dedicated Forwarding Script inside the Component Sandbox
            window.addEventListener('message', function(e) {{
                // Only forward valid events
                if (e.data && e.data.type && (e.data.type === 'FOCUS' || e.data.type === 'SYNC_DATA')) {{
                    const viewer = document.getElementById('viewer_iframe');
                    if (viewer) {{
                         viewer.contentWindow.postMessage(e.data, '*');
                    }}
                }}
            }});
        </script>
        """,
        height=700
    )

def relay_to_viewer(event_type, payload):
    """Sends message to the PARENT relay script, which handles cross-origin forwarding."""
    json_payload = json.dumps(payload)
    components.html(f"""<script>window.parent.postMessage({{type: '{event_type}', data: {json_payload}}}, '*');</script>""", height=0)

with col_data:
    st.subheader("Live Telemetry")
    selected_id = st.selectbox("Industrial Essence", list(machine_map.keys()), format_func=lambda x: machine_map[x]['name'])
    
    # RELAY CONTEXT: We send the FOCUS message separately from the telemetry fragment
    # to avoid race conditions and ensure it triggers exactly once on selection.
    if 'last_focus' not in st.session_state or st.session_state.last_focus != selected_id:
        relay_to_viewer('FOCUS', selected_id)
        st.session_state.last_focus = selected_id

    @st.fragment(run_every=1)
    def render_view():
        snapshot = generate_snapshot(machines)
        
        # Include pre-computed camera coordinates if available
        camera_coords = layout_data.get('camera_coords', {})
        for machine_id, coords in camera_coords.items():
            if machine_id in snapshot:
                snapshot[machine_id]['camera'] = coords
        
        relay_to_viewer('SYNC_DATA', snapshot)
        
        data = snapshot.get(selected_id)
        if data:
            st.info(f"**{data['display_name']}**")
            
            # Status and Trend Graph
            c1, c2 = st.columns([1, 2])
            c1.metric("Status", data['status'])
            
            # Plot Trend Graph for the first metric
            metrics_keys = list(data['metrics'].keys())
            first_metric_name = metrics_keys[0] if metrics_keys else "Utilization"
            hist_vals = st.session_state.history.get(f"{selected_id}_{first_metric_name}", [])
            
            fig_trend = go.Figure(go.Scatter(
                y=hist_vals, 
                mode='lines',
                line=dict(color='#00ff88', width=3),
                fill='tozeroy',
                fillcolor='rgba(0, 255, 136, 0.1)'
            ))
            fig_trend.update_layout(
                height=100, margin=dict(l=5,r=5,t=5,b=5),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            )
            c2.plotly_chart(fig_trend, width='stretch', key=f"trend_{selected_id}")
            
            st.markdown("---")
            for m_name, m_val in data['metrics'].items():
                cfg = generate_metrics_for_machine(data['display_name']).get(m_name, {})
                fig = go.Figure(go.Indicator(mode="gauge+number", value=m_val, title={'text': m_name, 'font': {'size': 14}}, gauge={'axis': {'range': cfg.get('range', [0, 100])}, 'bar': {'color': cfg.get('color', '#00d2ff')}}))
                fig.update_layout(height=160, margin=dict(l=30,r=30,t=40,b=20), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, width='stretch', key=f"gauge_{selected_id}_{m_name}")

    render_view()
