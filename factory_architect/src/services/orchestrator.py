import json
import shutil
import sys
from pathlib import Path
from loguru import logger

# Context
from src.core.context import ProjectContext
from src.models.schema import FactoryInput, LayoutSchema

# Services
from src.services.ai_engine import LayoutIntelligence, PlanerIntelligence
from src.services.dxf_engine import DXFRenderer

# Builder Import (Dynamic)
sys.path.append("/app") # Ensure root is in path
try:
    from factory_builder.main import FactoryBuilder
    BUILDER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Factory Builder not linked: {e}")
    BUILDER_AVAILABLE = False

class PipelineOrchestrator:
    def __init__(self, project_name: str):
        self.ctx = ProjectContext(project_name)
        self.ctx.initialize()
        
        # Agents
        self.planer = PlanerIntelligence()
        self.architect = LayoutIntelligence()

    def run(self):
        logger.info("="*60)
        logger.info(f"🚀 STARTING PIPELINE FOR: {self.ctx.project_name}")
        logger.info("="*60)

        # 1. Validation
        self.ctx.validate_input()

        # 2. Planning Phase (Input -> Intermediate JSON)
        factory_input = self._phase_planning()

        # 3. Architecture Phase (Intermediate JSON -> DXF + Debug)
        layout_schema = self._phase_architecture(factory_input)

        # 4. Handover Phase (Private -> Shared)
        self._phase_handover(factory_input, layout_schema)

        # 5. Construction Phase (Shared -> 3D Scene)
        if BUILDER_AVAILABLE:
            self._phase_construction()
        else:
            logger.warning("Construction phase skipped (Builder not found).")

    def _phase_planning(self) -> FactoryInput:
        logger.info("🧠 PHASE 1: Planning & Discovery")
        
        with open(self.ctx.source_entry_file, "r") as f:
            raw_data = json.load(f)

        # The Planer extracts structure from unstructured notes
        factory_input = self.planer.generate_input_schema(raw_data)
        
        # Save Intermediate Plan in Private Architect Folder
        with open(self.ctx.plan_json, "w") as f:
            json.dump(factory_input.model_dump(), f, indent=4)
            
        logger.success(f"✓ Plan generated: {self.ctx.plan_json}")
        return factory_input

    def _phase_architecture(self, data: FactoryInput) -> LayoutSchema:
        logger.info("📐 PHASE 2: Geometric Architecture")
        
        # The Architect embeds the graph into 2D space
        layout = self.architect.compute_layout(data)
        
        # Save Debug Data
        with open(self.ctx.debug_json, "w") as f:
            f.write(layout.model_dump_json(indent=2))

        # Render DXF
        renderer = DXFRenderer(str(self.ctx.dxf_output))
        renderer.render(layout)
        
        logger.success(f"✓ DXF generated: {self.ctx.dxf_output}")
        return layout

    def _phase_handover(self, data: FactoryInput, layout: LayoutSchema):
        logger.info("🤝 PHASE 3: Data Handover (Shared Bridge)")
        
        # 1. Copy DXF to Shared
        shutil.copy(self.ctx.dxf_output, self.ctx.shared_dxf)
        
        # 2. Create the Contract JSON for the Builder
        # The builder needs the semantic info (names, dims) combined with spatial info
        contract = {
            "project": self.ctx.project_name,
            "architecture_file": str(self.ctx.shared_dxf),
            "machines": [m.model_dump() for m in data.machines],
            "layout_coordinates": [m.model_dump() for m in layout.machines]
        }
        
        with open(self.ctx.shared_json, "w") as f:
            json.dump(contract, f, indent=4)
            
        logger.success(f"✓ Handover complete. Data ready in: {self.ctx.shared_root}")

    def _phase_construction(self):
        logger.info("🏗️ PHASE 4: 3D Construction")
        
        builder = FactoryBuilder(self.ctx)
        builder.execute()