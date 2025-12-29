"""
Centralized path management for deterministic folder structure.
Ensures all artifacts follow strict naming conventions.
"""
from pathlib import Path
import re
from typing import Optional


def sanitize_name(name: str) -> str:
    """Convert machine/project name to filesystem-safe name."""
    # Replace parentheses, slashes, and special chars with underscores
    safe = re.sub(r'[^\w\s-]', '_', name)
    # Replace spaces with underscores
    safe = re.sub(r'\s+', '_', safe)
    # Remove multiple consecutive underscores
    safe = re.sub(r'_+', '_', safe)
    return safe.strip('_')


class ProjectPaths:
    """
    Manages deterministic folder structure for a factory project.
    
    Structure:
        {output_dir}/{project_name}/
            ├── dxf/
            │   └── {project_name}.dxf
            ├── machines/
            │   ├── {machine_name}/
            │   │   ├── image/
            │   │   │   └── {machine_name}.jpg
            │   │   └── glb/
            │   │       └── {machine_name}.glb
            └── scene/
                └── {project_name}_complete.glb
    """
    
    def __init__(self, output_dir: Path, project_name: str):
        self.output_dir = Path(output_dir)
        self.project_name = project_name
        self.safe_project_name = sanitize_name(project_name)
        
        # Root project directory
        self.project_root = self.output_dir / self.safe_project_name
        
        # Main subdirectories
        self.dxf_dir = self.project_root / "dxf"
        self.machines_dir = self.project_root / "machines"
        self.scene_dir = self.project_root / "scene"
    
    def setup(self):
        """Create all necessary directories."""
        self.dxf_dir.mkdir(parents=True, exist_ok=True)
        self.machines_dir.mkdir(parents=True, exist_ok=True)
        self.scene_dir.mkdir(parents=True, exist_ok=True)
        return self
    
    def get_dxf_path(self) -> Path:
        """Get path for the DXF file."""
        return self.dxf_dir / f"{self.safe_project_name}.dxf"
    
    def get_machine_dir(self, machine_name: str) -> Path:
        """Get directory for a specific machine."""
        safe_name = sanitize_name(machine_name)
        return self.machines_dir / safe_name
    
    def get_machine_image_path(self, machine_name: str) -> Path:
        """Get path for machine image."""
        machine_dir = self.get_machine_dir(machine_name)
        image_dir = machine_dir / "image"
        image_dir.mkdir(parents=True, exist_ok=True)
        safe_name = sanitize_name(machine_name)
        return image_dir / f"{safe_name}.jpg"
    
    def get_machine_glb_path(self, machine_name: str) -> Path:
        """Get path for machine GLB file."""
        machine_dir = self.get_machine_dir(machine_name)
        glb_dir = machine_dir / "glb"
        glb_dir.mkdir(parents=True, exist_ok=True)
        safe_name = sanitize_name(machine_name)
        return glb_dir / f"{safe_name}.glb"
    
    def get_scene_path(self) -> Path:
        """Get path for final complete scene."""
        return self.scene_dir / f"{self.safe_project_name}_complete.glb"
    
    def get_debug_layout_path(self) -> Path:
        """Get path for debug layout JSON."""
        return self.project_root / "debug_layout.json"
