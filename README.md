# 🏭 AI Factory Generator

**Automated Industrial Layout & 3D Visualization Pipeline**

This system converts a high-level factory definition (`input.json`) into a complete, 3D-visualized factory floor scene (`.glb`) automatically. It uses Generative AI for layout optimization and 3D Model Generation.

---

## 🚀 Quick Start

### 1. Prerequisites

- **Docker** installed.
- **Ngrok URL** (for Colab GPU backend).
- **Google GenAI API Key**.

### 2. Configuration

Create a `.env` file in the root directory:

```env
GOOGLE_API_KEY=your_google_api_key
API_URL=https://your-ngrok-url.ngrok-free.dev/generate
```

### 3. Run the Pipeline

Place your factory definition in `data/input.json`. Then run:

```bash
docker compose up --build
```

The system will:

1.  **Scrape** images for all machines from the web.
2.  **Generate** an optimized DXF floor plan (using Factory Architect).
3.  **Create** 3D models for each machine (using Factory Builder + Cloud GPU).
4.  **Assemble** the final scene with piping and connections.

### 4. Output

Artifacts are saved to `data/output/{ProjectName}/`:

- `scene/*_complete.glb`: The final 3D file (viewable in Windows 3D Viewer or online GLB viewers).
- `dxf/*.dxf`: The CAD layout.

---

## 🏗️ Architecture

The solution is packaged as a single Docker container containing two integrated modules:

### 1. Factory Architect

- **Role**: Intelligence & Layout.
- **Input**: `input.json` (Machines & Connections).
- **Process**: Uses Google Gemini to optimize placement. Generates a DXF file with strict dimensions in XDATA.
- **Output**: `.dxf` file with detailed machine metadata.

### 2. Factory Builder

- **Role**: 3D Generation & Assembly.
- **Input**: generated `.dxf`.
- **Process**:
  - **Scraping**: Finds real-world images of machines.
  - **3D Gen**: Sends images to Cloud GPU (Colab) to generate GLB models.
  - **Composing**: Replaces DXF blocks with 3D models, connecting them with pipes.
- **Output**: Final `.glb` scene.

---

## 🛠️ Advanced Configuration

### Environment Variables

| Variable              | Default  | Description                                                 |
| :-------------------- | :------- | :---------------------------------------------------------- |
| `MAX_WORKERS`         | `1`      | Concurrency for cloud uploads. Keep at 1 for serial queues. |
| `API_TIMEOUT`         | `1200`   | Timeout (seconds) for 3D generation.                        |
| `TARGET_MACHINE_SIZE` | `3000.0` | Default normalization size (mm) for models.                 |

### Serial Processing

The cloud client is optimized for **Serial Processing** (`MAX_WORKERS=1`) with robust retry logic. This ensures 100% success rate even when the backend GPU server processes one request at a time.

---

## 📁 Directory Structure

```
/
├── data/                  # Mount this volume!
│   ├── input.json         # Your input file
│   └── output/            # Generated results
├── factory_architect/     # Source code (Layout Engine)
├── factory_builder/       # Source code (3D Engine)
├── Dockerfile             # Unified container definition
└── docker-compose.yml     # Orchestration
```
