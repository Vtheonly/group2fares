from dataclasses import dataclass, field
from typing import List, Tuple, Optional

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
    dimensions: Tuple[float, float] = (2000.0, 2000.0)  # Length, Width
    
    # Dynamic Paths (Set during asset acquisition)
    image_path: Optional[str] = None
    model_path: Optional[str] = None
    
    @property
    def clean_name(self) -> str:
        """Returns a filename-safe version of the name."""
        import re
        safe = re.sub(r'[^\w\s-]', '_', self.name)
        safe = re.sub(r'\s+', '_', safe)
        return safe.strip('_')

@dataclass
class ProductionLine:
    """Represents a connection/pipe between machines."""
    id: str
    from_id: str
    to_id: str
    conn_type: str  # 'pump_line', 'conveyor', etc.
    vertices: List[Vector3] = field(default_factory=list)

@dataclass
class FactoryLayout:
    """Represents the entire floor plan."""
    source_file: str
    width: float
    height: float
    center: Vector3
    entities: List[FactoryEntity] = field(default_factory=list)
    production_lines: List[ProductionLine] = field(default_factory=list)