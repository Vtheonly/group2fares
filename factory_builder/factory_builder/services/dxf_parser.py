import ezdxf
from factory_builder.domain import FactoryLayout, FactoryEntity, ProductionLine, Vector3
from factory_builder.utils import get_logger

log = get_logger("DxfParser")

class DxfParser:
    def parse(self, filepath: str) -> FactoryLayout:
        log.info(f"Parsing DXF Contract: {filepath}")
        
        try:
            doc = ezdxf.readfile(filepath)
            msp = doc.modelspace()
        except Exception as e:
            log.error(f"Failed to read DXF file: {e}")
            raise

        entities = []
        production_lines = []
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')

        # 1. Iterate over Modelspace
        for e in msp:
            try:
                # --- A. Block References (Machines) ---
                if e.dxftype() == 'INSERT':
                    x, y, _ = e.dxf.insert
                    rotation = getattr(e.dxf, 'rotation', 0)
                    
                    # Defaults
                    machine_name = e.dxf.name
                    machine_id = str(e.dxf.handle)
                    length, width = 2000.0, 2000.0
                    
                    # Extract Semantic Data from XDATA (The Contract)
                    if e.has_xdata("FACTORY_ARCHITECT"):
                        xdata = e.get_xdata("FACTORY_ARCHITECT")
                        for code, value in xdata:
                            if code == 1000:
                                if value.startswith("NAME:"):
                                    machine_name = value[5:]
                                elif value.startswith("ID:"):
                                    machine_id = value[3:]
                                elif value.startswith("LENGTH:"):
                                    length = float(value[7:])
                                elif value.startswith("WIDTH:"):
                                    width = float(value[6:])
                    
                    # Update Scene Bounds
                    min_x, max_x = min(min_x, x), max(max_x, x)
                    min_y, max_y = min(min_y, y), max(max_y, y)

                    entities.append(FactoryEntity(
                        id=machine_id,
                        name=machine_name,
                        type="MACHINE",
                        position=Vector3(x, y),
                        rotation=rotation,
                        dimensions=(length, width)
                    ))

                # --- B. Polylines (Production Lines/Pipes) ---
                elif e.dxftype() == 'LWPOLYLINE':
                    if e.has_xdata("FACTORY_ARCHITECT"):
                        xdata = e.get_xdata("FACTORY_ARCHITECT")
                        is_connection = False
                        from_id = to_id = conn_type = ""
                        
                        for code, value in xdata:
                            if code == 1000:
                                if value == "TYPE:CONNECTION_EDGE":
                                    is_connection = True
                                elif value.startswith("FROM:"):
                                    from_id = value[5:]
                                elif value.startswith("TO:"):
                                    to_id = value[3:]
                                elif value.startswith("CONN_TYPE:"):
                                    conn_type = value[10:]
                        
                        if is_connection:
                            # Convert Polyline points to Vectors
                            points = e.get_points() # format: [(x,y,0,0,0), ...]
                            vertices = [Vector3(p[0], p[1]) for p in points]
                            
                            production_lines.append(ProductionLine(
                                id=str(e.dxf.handle),
                                from_id=from_id,
                                to_id=to_id,
                                conn_type=conn_type,
                                vertices=vertices
                            ))

            except Exception as err:
                log.warning(f"Skipping corrupt entity: {err}")

        # Calculate Floor Dimensions
        width = max_x - min_x if max_x > min_x else 10000
        height = max_y - min_y if max_y > min_y else 10000
        center = Vector3(min_x + width/2, min_y + height/2)

        return FactoryLayout(str(filepath), width, height, center, entities, production_lines)