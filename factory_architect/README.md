# 🏭 Factory Architect 5.0

**Factory Architect** is an Industry 5.0 generative CAD system that transforms unstructured project notes into professional, semantically rich 2D factory layouts. It uses a two-stage Multi-Agent pipeline to bridge the gap between high-level industrial intent and precise geometric engineering.

## 🚀 How it Works (Tick & Tock)

The system operates as a **two-stage industrial brain**:

### Stage 1: The Planer Agent (Discovery)

When you provide raw project notes (`main_entry.json`), the **Planer Agent** (powered by Gemini 2.5/3 Pro) analyzes the text to:

- **Indentify**: Extract a primary production line (e.g., SPC Flooring, Injection Molding).
- **Engineer**: Define the machine list, estimate realistic dimensions (mm), and establish topological relationships (the "Graph").
- **Output**: Generates a structured `input.json` that acts as the engineering contract.

### Stage 2: The Architect Agent (Physics & Layout)

The **Architect Agent** takes the structured plan and acts as a **Layout Physics Engine**:

- **Graph Embedding**: It maps the abstract flow onto a 2D floorplan.
- **Rule Enforcement**: It applies strict industrial rules:
  - **Snake Flow**: Efficient use of space by turning lines 90/180°.
  - **Physical Clearance**: Automatic 1500mm safety buffers.
  - **Port Alignment**: Rotating machines to optimize connection paths.
- **CAD Synthesis**: Uses `ezdxf` to generate a professional `.dxf` file.

## 💎 Features

- **Semantic DXF**: Every machine and connection is drawn on dedicated layers with appropriate colors and linetypes (Conveyors, Pipes, AGV Paths).
- **Invisible Intelligence (XDATA)**: Every CAD entity is embedded with invisible metadata (ID, Type, Source/Target) for downstream system integration.
- **Manhattan Routing**: All production lines are connected using orthogonal paths (90° turns).
- **Dockerized Environment**: Zero-config execution with all CAD fonts and dependencies pre-configured.

## 🛠 Prerequisites

- **Docker** and **Docker Compose**
- A **Google Gemini API Key** (Direct API or via OpenRouter)

## 🚦 Getting Started

### 1. Configure Credentials

Create a `.env` file in the `factory_architect/` directory:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 2. Prepare Input

- Place your project notes in `factory_architect/data/main_entry.json`.
- _(Optional)_ If you already have a floorplan plan, skip the planer by providing `factory_architect/data/input.json` directly.

### 3. Launch Docker

Run the following command to build and execute the pipeline:

```bash
cd factory_architect
docker compose up --build
```

## 📂 Project Structure

```text
factory_architect/
├── data/
│   ├── main_entry.json   <-- [INPUT] Your project notes
│   ├── input.json        <-- [AUTO] Generated production line plan
│   └── output/           <-- [FINAL] DXF and Debug JSON files
├── src/
│   ├── main.py           <-- Orchestrator (Stage 1 & 2 Manager)
│   ├── core/config.py    <-- Pydantic settings & model selection
│   ├── models/schema.py  <-- Strict data contracts
│   └── services/
│       ├── ai_engine.py  <-- The Brain (Planer & Layout Agents)
│       └── dxf_engine.py <-- The CAD Engine (ezdxf renderer)
└── Dockerfile            <-- Headless Python CAD environment
```

## 🔍 Verification

To verify the hidden "flags" (XDATA) embedded in the DXF file:

```bash
docker compose run --rm --entrypoint python architect src/verify_flags.py /app/data/output/Your_Project_Name.dxf
```

---

_Developed for SARL ALLO MAISON - Advanced Material Complexes._
