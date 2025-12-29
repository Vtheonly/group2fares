# Factory Orchestration - Complete Pipeline

## Quick Start

```bash
# 1. Create shared data directory with input.json
mkdir -p shared_data
cp factory_architect/data/input.json shared_data/

# 2. Set your Colab/Ngrok URL
export API_URL="https://your-ngrok-url.ngrok-free.dev/generate"

# 3. Run orchestration
docker compose up --build architect
```

## What It Does

**End-to-end pipeline:**

1. **Extracts** all machine names from input.json (exact names preserved)
2. **Scrapes** images for each machine via DuckDuckGo
3. **Generates** DXF factory layout using AI
4. **Builds** 3D models via Cloud API (Colab/Ngrok)
5. **Assembles** final scene with all machines positioned correctly

## Folder Structure

All outputs organized deterministically:

```
shared_data/output/
  └── {project_name}/
      ├── dxf/
      │   └── {project_name}.dxf
      ├── machines/
      │   ├── {machine_name_1}/
      │   │   ├── image/
      │   │   │   └── {machine_name_1}.jpg
      │   │   └── glb/
      │   │       └── {machine_name_1}.glb
      │   └── {machine_name_2}/
      │       ├── image/
      │       └── glb/
      └── scene/
          └── {project_name}_complete.glb
```

## Services

- **architect**: Orchestrates pipeline (scraping → DXF → 3D → scene)
- **builder**: Standalone 3D generation (optional)

## Requirements

- Docker & Docker Compose
- Gemini API key (in `factory_architect/.env`)
- Colab/Ngrok endpoint for 3D generation
