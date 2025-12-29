from dataclasses import dataclass, field
from typing import Optional, List, Tuple

@dataclass
class Vector3:
    x: float
    y: float
    z: float = 0.0

@dataclass
class FactoryEntity:
    """Represents a single object found in the DXF."""
    id: str
    name: str
    type: str  # 'MACHINE', 'TEXT', 'PORT'
    position: Vector3
    rotation: float = 0.0
    
    # Processing State
    image_path: Optional[str] = None
    model_path: Optional[str] = None
    
    @property
    def clean_name(self) -> str:
        """Returns a filename-safe version of the name."""
        return "".join([c if c.isalnum() else "_" for c in self.name]).strip()

@dataclass
class FactoryLayout:
    """Represents the entire floor plan."""
    source_file: str
    width: float
    height: float
    center: Vector3
    entities: List[FactoryEntity] = field(default_factory=list)
