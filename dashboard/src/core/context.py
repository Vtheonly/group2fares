import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ProjectReference:
    name: str
    contract_path: Path
    camera_map_path: Path
    scene_path: Path

class TwinContext:
    """
    Manages access to the Shared Data Bridge and Builder Outputs.
    """
    def __init__(self):
        # Paths mapped via Docker
        self.shared_root = Path("/app/shared_data")
        self.builder_root = Path("/app/factory_builder/data")
    
    def discover_projects(self) -> List[ProjectReference]:
        """Scans shared_data for projects that have a valid contract."""
        projects = []
        if not self.shared_root.exists():
            return []

        for folder in self.shared_root.iterdir():
            if folder.is_dir():
                contract = folder / "layout_contract.json"
                # The scene lives in the Builder's private storage, but we mount it for reading
                scene_dir = self.builder_root / folder.name / "scene"
                scene_file = scene_dir / "factory_complete.glb"
                cam_map = self.shared_root / folder.name / "camera_map.json"

                if contract.exists() and scene_file.exists():
                    projects.append(ProjectReference(
                        name=folder.name,
                        contract_path=contract,
                        camera_map_path=cam_map,
                        scene_path=scene_file
                    ))
        
        # Sort by newest
        projects.sort(key=lambda p: p.contract_path.stat().st_mtime, reverse=True)
        return projects