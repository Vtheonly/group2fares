from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# --- Geometry Helpers ---
class Dimensions(BaseModel):
    length: float
    width: float

class Point2D(BaseModel):
    x: float
    y: float

# --- Input Schemas ---
class MachineInput(BaseModel):
    id: str
    name: str
    length: float
    width: float

class RelationshipInput(BaseModel):
    from_id: str
    to_id: str
    type: str = Field(default="conveyor", description="Type of connection: conveyor, pipe, agv, etc.")

class FactoryInput(BaseModel):
    project_name: str
    process_description: str = Field(..., description="Natural language description of the flow and constraints.")
    machines: List[MachineInput]
    relationships: List[RelationshipInput]

# --- Output/Calculated Schemas ---
class PlacedMachine(BaseModel):
    id: str
    name: str
    dimensions: Dimensions
    position: Point2D
    rotation: float = Field(..., description="Rotation in degrees (0, 90, 180, 270)")
    
class FlowPath(BaseModel):
    from_machine_id: str
    to_machine_id: str
    connection_type: str
    path_points: List[Point2D] = Field(..., description="List of X,Y points tracing the path")

class LayoutSchema(BaseModel):
    room_width: float
    room_height: float
    machines: List[PlacedMachine]
    flow_connections: List[FlowPath]
