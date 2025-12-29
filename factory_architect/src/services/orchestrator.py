"""
Orchestrator service - connects all pipeline stages end-to-end.
Manages: image scraping → DXF generation → 3D model building → scene assembly
"""
import json
import sys
from pathlib import Path
from loguru import logger

# Add factory_builder to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "factory_builder"))

from src.models.schema import FactoryInput, LayoutSchema
from src.services.ai_engine import LayoutIntelligence
from src.services.dxf_engine import DXFRenderer
from src.services.scraper_client import ScraperClient
from src.core.paths import ProjectPaths

try:
    from factory_builder.services.cloud_client import CloudRenderer
    from factory_builder.services.scene_composer import SceneComposer
    from factory_builder.domain import FactoryEntity, Vector3, FactoryLayout
    BUILDER_AVAILABLE = True
except ImportError:
    logger.warning("factory_builder modules not fully available")
    BUILDER_AVAILABLE = False


class FactoryOrchestrator:
    """
    Orchestrates the complete factory generation pipeline.
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.scraper = ScraperClient()
        self.layout_ai = LayoutIntelligence()
    
    def execute(self, factory_input: FactoryInput) -> Path:
        """
        Execute the complete pipeline in strict sequential batches.
        
        1. Batch Scrape All Images
        2. Generate DXF Layout
        3. Batch Generate All 3D Models
        4. Merge/Assemble Final Scene
        """
        logger.info("=" * 60)
        logger.info("🏭 FACTORY ORCHESTRATION PIPELINE - STRICT SEQUENCE")
        logger.info("=" * 60)
        
        # Initialize path structure (still used for DXF/Scene organization)
        paths = ProjectPaths(self.output_dir, factory_input.project_name).setup()
        
        # --- PHASE 1: BATCH SCRAPE (Sequential) ---
        logger.info("\n📸 PHASE 1: Batch Image Acquisition")
        logger.info("-" * 60)
        image_results = self._batch_scrape_images(factory_input)
        
        # --- PHASE 2: DXF GENERATION ---
        logger.info("\n📐 PHASE 2: DXF Layout Generation")
        logger.info("-" * 60)
        layout = self._generate_dxf(factory_input, paths)
        
        # --- PHASE 3: BATCH 3D GENERATION (Sequential) ---
        logger.info("\n🎨 PHASE 3: Batch 3D Model Generation")
        logger.info("-" * 60)
        model_results = self._batch_generate_3d_models(factory_input, image_results)
        
        # --- PHASE 4: FINAL MERGE ---
        logger.info("\n🏗️ PHASE 4: Final Scene Merge")
        logger.info("-" * 60)
        scene_path = self._merge_scene(factory_input, paths, layout, model_results)
        
        logger.info("\n" + "=" * 60)
        logger.success("🎉 PIPELINE COMPLETE")
        logger.info("=" * 60)
        logger.info(f"📁 Project Root: {paths.project_root}")
        logger.info(f"📐 DXF Layout: {paths.get_dxf_path()}")
        logger.info(f"🎨 Final Scene: {scene_path}")
        
        return scene_path
    
    def _batch_scrape_images(self, factory_input: FactoryInput) -> dict[str, bool]:
        """Phase 1: Sequentially scrape images for ALL machines."""
        machine_names = [m.name for m in factory_input.machines]
        
        # Call updated scraper client (no path mapping needed, saving to strict input dir)
        results = self.scraper.scrape_all_machines(machine_names)
        
        successful = sum(1 for v in results.values() if v)
        logger.success(f"✓ Batch scrape complete: {successful}/{len(machine_names)}")
        
        return results

    def _generate_dxf(self, factory_input: FactoryInput, paths: ProjectPaths) -> LayoutSchema:
        """Phase 2: Generate DXF layout using AI."""
        # Compute layout
        layout = self.layout_ai.compute_layout(factory_input)
        
        # Save debug layout
        debug_path = paths.get_debug_layout_path()
        with open(debug_path, "w") as f:
            f.write(layout.model_dump_json(indent=2))
        logger.info(f"Debug layout saved: {debug_path}")
        
        # Render DXF
        dxf_path = paths.get_dxf_path()
        renderer = DXFRenderer(str(dxf_path))
        renderer.render(layout)
        
        logger.success(f"✓ DXF generated: {dxf_path}")
        
        return layout
    
    def _batch_generate_3d_models(
        self, 
        factory_input: FactoryInput, 
        image_results: dict[str, bool]
    ) -> dict[str, Path]:
        """Phase 3: Sequentially generate 3D models for ALL machines."""
        
        if not BUILDER_AVAILABLE:
            logger.warning("⚠️ Factory builder not available - skipping 3D generation")
            return {}
            
        from factory_builder.config import Config
        from src.core.paths import sanitize_name
        
        cloud_renderer = CloudRenderer()
        results = {}
        
        total = len(factory_input.machines)
        logger.info(f"Starting batch 3D generation for {total} machines...")
        
        for i, machine in enumerate(factory_input.machines, 1):
            logger.info(f"[{i}/{total}] Processing 3D: {machine.name}")
            
            # Check if image exists (from Phase 1)
            safe_name = sanitize_name(machine.name)
            image_path = Config.INPUT_DIR / f"{safe_name}.png"
            
            if not image_path.exists():
                logger.warning(f"Skipping {machine.name} (image missing: {image_path})")
                continue

            # Strict Output Path: factory_builder/output/{MachineName}/{MachineName}.glb
            # We use the sanitized name for the folder and file to be safe
            machine_output_dir = Config.OUTPUT_DIR / safe_name
            machine_output_dir.mkdir(parents=True, exist_ok=True)
            target_glb_path = machine_output_dir / f"{safe_name}.glb"
            
            # Check cache
            if target_glb_path.exists():
                logger.info(f"Using cached model: {target_glb_path}")
                results[machine.name] = target_glb_path
                continue
            
            # Create entity for Cloud Client
            entity = FactoryEntity(
                id=machine.id,
                name=machine.name,
                type="MACHINE",
                position=Vector3(0, 0),
                image_path=str(image_path)
            )
            
            # Generate
            try:
                # cloud_renderer._upload_and_stream saves to models_dir by default
                # We need to move it to our target structure
                generated_path = cloud_renderer._upload_and_stream(entity)
                
                if generated_path and Path(generated_path).exists():
                    import shutil
                    shutil.move(generated_path, target_glb_path)
                    results[machine.name] = target_glb_path
                    logger.success(f"✓ Model generated: {target_glb_path}")
                else:
                    logger.warning(f"✗ Generation failed for: {machine.name}")
            
            except Exception as e:
                logger.error(f"Error generating {machine.name}: {e}")
                
        logger.success(f"✓ Batch 3D complete: {len(results)}/{total}")
        return results
    
    def _merge_scene(
        self,
        factory_input: FactoryInput,
        paths: ProjectPaths,
        layout: LayoutSchema,
        model_results: dict[str, Path]
    ) -> Path:
        """Phase 4: Merge individual GLBs into final scene."""
        
        if not BUILDER_AVAILABLE:
            logger.warning("⚠️ Factory builder not available - skipping merge")
            return paths.get_scene_path()
        
        from factory_builder.config import Config

        # Prepare entities with correct positions and model paths
        entities = []
        for placed_machine in layout.machines:
            input_machine = next(
                (m for m in factory_input.machines if m.id == placed_machine.id),
                None
            )
            if not input_machine: continue
            
            model_path = model_results.get(input_machine.name)
            
            entity = FactoryEntity(
                id=placed_machine.id,
                name=input_machine.name,
                type="MACHINE",
                position=Vector3(placed_machine.position.x, placed_machine.position.y, 0),
                rotation=placed_machine.rotation,
                model_path=str(model_path) if model_path else None
            )
            entities.append(entity)
            
        # Create Factory Layout
        factory_layout = FactoryLayout(
            source_file=str(paths.get_dxf_path()),
            width=layout.room_width,
            height=layout.room_height,
            center=Vector3(layout.room_width/2, layout.room_height/2, 0),
            entities=entities
        )
        
        # Merge
        # We need to save to /app/factory_builder/output/{FactoryName}_Merged.glb
        safe_project_name = paths.safe_project_name
        merged_filename = f"{safe_project_name}_Merged.glb"
        merged_path = Config.OUTPUT_DIR / merged_filename
        
        composer = SceneComposer()
        composer.build(factory_layout, merged_filename)
        
        # SceneComposer saves to Config.OUTPUT_DIR by default
        # Verify it exists
        if merged_path.exists():
            logger.success(f"✓ Merged scene saved: {merged_path}")
            return merged_path
        else:
            logger.error(f"❌ Merge failed. File not found: {merged_path}")
            return paths.get_scene_path() # Fallback
