import streamlit as st
import streamlit.components.v1 as components
import time
import random
import pandas as pd
import plotly.graph_objects as go
import json
import os

# ==========================================
# 1. CONFIG & LAYOUT
# ==========================================
st.set_page_config(layout="wide", page_title="Factory 5.0 Twin Dashboard")

# Custom CSS for the "Digital Twin" look
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    div.block-container { padding-top: 1.5rem; }
    
    /* Premium font and styling */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .metric-container {
        border-right: 1px solid #333;
        padding: 10px;
    }
    
    h1, h2, h3 { color: #00d2ff !important; font-weight: 600 !important; }
    
    /* Modern scrollbar */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #0e1117; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# Extended Machine Config
METRIC_CONFIG = {
    "mixer": {
        "metrics": {
            "Mixing Speed": {"unit": "RPM", "range": [0, 2000], "target": 1450, "color": "#00d2ff"},
            "Motor Torque": {"unit": "Nm", "range": [0, 800], "target": 520, "color": "#00ff88"},
            "Internal Temp": {"unit": "°C", "range": [20, 120], "target": 85, "color": "#ffaa00"}
        },
        "description": "High-viscosity intensive mixing unit for advanced polymer composites."
    },
    "extruder": {
        "metrics": {
            "Melt Pressure": {"unit": "Bar", "range": [0, 400], "target": 285, "color": "#ff0055"},
            "Screw Frequency": {"unit": "Hz", "range": [0, 120], "target": 72, "color": "#00d2ff"},
            "Barrel Temp": {"unit": "°C", "range": [150, 350], "target": 245, "color": "#ffaa00"}
        },
        "description": "Twin-screw precision extruder with integrated heating zones."
    },
    "calender": {
        "metrics": {
            "Roll Gap": {"unit": "mm", "range": [0.1, 5.0], "target": 1.2, "color": "#00ff88"},
            "Line Velocity": {"unit": "m/s", "range": [0, 20], "target": 8.5, "color": "#00d2ff"},
            "Linear Load": {"unit": "kg/cm", "range": [0, 500], "target": 310, "color": "#ffaa00"}
        },
        "description": "Multistage calendering unit for high-uniformity film production."
    },
    "cooler": {
        "metrics": {
            "Water Flow": {"unit": "L/min", "range": [0, 100], "target": 65, "color": "#00d2ff"},
            "Input Temp": {"unit": "°C", "range": [10, 50], "target": 18, "color": "#00ff88"},
            "Cooling Power": {"unit": "kW", "range": [0, 50], "target": 32, "color": "#ff0055"}
        },
        "description": "Closed-loop industrial cooling station."
    },
    "cutter": {
        "metrics": {
            "Cycle Rate": {"unit": "ppm", "range": [0, 200], "target": 145, "color": "#ff0055"},
            "Blade State": {"unit": "%", "range": [0, 100], "target": 88, "color": "#00ff88"},
            "Precision": {"unit": "mm", "range": [0, 1], "target": 0.05, "color": "#00d2ff"}
        },
        "description": "Ultrasonic precision cutting mechanism."
    },
    "packer": {
        "metrics": {
            "Pack Speed": {"unit": "u/min", "range": [0, 100], "target": 68, "color": "#00d2ff"},
            "Error Rate": {"unit": "%", "range": [0, 5], "target": 0.2, "color": "#ff0055"},
            "Vacuum Level": {"unit": "kPa", "range": [-100, 0], "target": -82, "color": "#00ff88"}
        },
        "description": "Automated vacuum packaging and labeling unit."
    },
    "default": {
        "metrics": {
            "Operational Load": {"unit": "%", "range": [0, 100], "target": 78, "color": "#00d2ff"},
            "Energy Intake": {"unit": "kW", "range": [0, 200], "target": 92, "color": "#ffaa00"}
        },
        "description": "Generic auxiliary industrial node."
    }
}

# ==========================================
# 2. DIGITAL TWIN LOGIC
# ==========================================
class DigitalTwinSim:
    def __init__(self):
        # Precise IDs used in the GLB
        self.machines = ["m_mixer", "m_extruder", "m_calender", "m_cooler", "m_cutter", "m_profiler", "m_packer"]
    
    def get_config(self, m_id):
        for key in METRIC_CONFIG:
            if key in m_id.lower():
                return METRIC_CONFIG[key]
        return METRIC_CONFIG["default"]

    def generate_snapshot(self):
        data = {}
        for m in self.machines:
            cfg = self.get_config(m)
            m_metrics = {}
            for name, details in cfg["metrics"].items():
                target = details["target"]
                noise = (details["range"][1] - details["range"][0]) * 0.04
                val = target + random.uniform(-noise, noise)
                m_metrics[name] = round(max(details["range"][0], min(details["range"][1], val)), 2)
            
            data[m] = {
                "metrics": m_metrics,
                "status": "Running" if random.random() > 0.05 else "Maintenance",
                "health": round(random.uniform(92, 100), 1),
                "desc": cfg["description"]
            }
        return data

if 'sim' not in st.session_state:
    st.session_state.sim = DigitalTwinSim()

# ==========================================
# 3. COMMUNICATION BRIDGE
# ==========================================
def push_to_viewer(type, payload):
    """Broadcasts data to the 3D viewer iframe."""
    components.html(f"""
        <script>
            const viewer = window.parent.document.querySelector('iframe[title="factory_viewer"]');
            if (viewer && viewer.contentWindow) {{
                viewer.contentWindow.postMessage({{type: '{type}', data: {json.dumps(payload)}}}, '*');
            }}
        </script>
    """, height=0)

# ==========================================
# 4. DASHBOARD UI
# ==========================================
st.title("💠 Factory 5.0: Advanced Digital Twin")

col_3d, col_dash = st.columns([3, 2])

with col_3d:
    MODEL_FILE = "ALLO_MAISON_Complexe_Industriel_Polymère_Matériaux_Avancés_scene_gray.glb"
    components.html(
        f"""
        <iframe 
            src="http://localhost:8000/static/viewer.html?model={MODEL_FILE}" 
            width="100%" height="650px" 
            title="factory_viewer"
            style="border:1px solid #333; border-radius:12px; box-shadow: 0 0 30px rgba(0,0,0,0.5);"
        ></iframe>
        """,
        height=670
    )

with col_dash:
    st.subheader("Control & Analytics")
    
    selection = st.selectbox(
        "Focus Industrial Entity", 
        st.session_state.sim.machines,
        format_func=lambda x: x.replace("m_", "").upper(),
        key="main_selector"
    )

    # Trigger snap on change
    if 'old_sel' not in st.session_state or st.session_state.old_sel != selection:
        push_to_viewer('FOCUS', selection)
        st.session_state.old_sel = selection

    @st.fragment(run_every=1)
    def render_live_view():
        snapshot = st.session_state.sim.generate_snapshot()
        
        # Periodic sync of all machine data to the viewer (for tooltips)
        push_to_viewer('SYNC_DATA', snapshot)
        
        m_data = snapshot.get(selection)
        if not m_data: return

        # Header Info
        st.info(f"**ID:** {selection.upper()} | **Status:** {m_data['status']}")
        st.caption(m_data['desc'])
        
        # Health Progress Bar
        h_color = "green" if m_data['health'] > 95 else "orange"
        st.markdown(f"**Structural Integrity / Health:** {m_data['health']}%")
        st.progress(m_data['health'] / 100)

        st.divider()
        
        # Premium Indicators
        for name, val in m_data["metrics"].items():
            cfg = st.session_state.sim.get_config(selection)["metrics"][name]
            
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = val,
                delta = {'reference': cfg['target'], 'increasing': {'color': "#00ff88"}, 'decreasing': {'color': "#ff0055"}},
                number = {'suffix': f" {cfg['unit']}", 'font': {'size': 24, 'color': 'white'}},
                title = {'text': name.upper(), 'font': {'size': 14, 'color': '#888'}},
                gauge = {
                    'axis': {'range': cfg['range'], 'tickwidth': 1, 'tickcolor': "#444"},
                    'bar': {'color': cfg['color']},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 2,
                    'bordercolor': "#333",
                    'steps': [
                        {'range': [cfg['range'][0], cfg['target']*0.8], 'color': 'rgba(255,255,255,0.05)'},
                        {'range': [cfg['target']*1.1, cfg['range'][1]], 'color': 'rgba(255,255,255,0.05)'}
                    ],
                    'threshold': {
                        'line': {'color': "white", 'width': 4},
                        'thickness': 0.75,
                        'value': cfg['target']
                    }
                }
            ))
            
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=40, b=20),
                height=180
            )
            st.plotly_chart(fig, width='stretch')

    render_live_view()
