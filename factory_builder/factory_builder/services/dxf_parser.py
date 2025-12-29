import ezdxf
from factory_builder.domain import FactoryLayout, FactoryEntity, ProductionLine, Vector3
from factory_builder.utils import get_logger

log = get_logger("DXF_Parser")

class DxfParser:
    def parse(self, filepath: str) -> FactoryLayout:
        log.info(f"Parsing DXF: {filepath}")
        
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

        for e in msp:
            try:
                # 1. Block References (Machines)
                if e.dxftype() == 'INSERT':
                    x, y, _ = e.dxf.insert
                    block_name = e.dxf.name
                    rotation = getattr(e.dxf, 'rotation', 0)
                    
                    # Extract machine name from XDATA if available
                    machine_name = block_name  # Default to block name
                    machine_id = None
                    length, width = 2000.0, 2000.0
                    
                    if e.has_xdata("FACTORY_ARCHITECT"):
                        xdata = e.get_xdata("FACTORY_ARCHITECT")
                        for code, value in xdata:
                            if code == 1000:  # String data
                                if value.startswith("NAME:"):
                                    machine_name = value[5:]  # Remove "NAME:" prefix
                                elif value.startswith("ID:"):
                                    machine_id = value[3:]
                                elif value.startswith("LENGTH:"):
                                    try: length = float(value[7:])
                                    except: pass
                                elif value.startswith("WIDTH:"):
                                    try: width = float(value[6:])
                                    except: pass
                    
                    # Track bounds
                    min_x, max_x = min(min_x, x), max(max_x, x)
                    min_y, max_y = min(min_y, y), max(max_y, y)

                    entities.append(FactoryEntity(
                        id=machine_id or str(e.dxf.handle),
                        name=machine_name,
                        type="MACHINE",
                        position=Vector3(x, y),
                        rotation=rotation,
                        dimensions=(length, width)
                    ))

                # 2. Production Lines (Polylines with XDATA)
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
                            vertices = [Vector3(p[0], p[1]) for p in e.get_points()]
                            production_lines.append(ProductionLine(
                                id=str(e.dxf.handle),
                                from_id=from_id,
                                to_id=to_id,
                                conn_type=conn_type,
                                vertices=vertices
                            ))
                            log.debug(f"Found connection: {from_id} -> {to_id}")

                # 3. Text (Labels, Ports)
                elif e.dxftype() in ['TEXT', 'MTEXT']:
                    text = e.dxf.text if hasattr(e.dxf, 'text') else e.text
                    x, y, _ = e.dxf.insert
                    
                    entity_type = "PORT" if "IN" in text or "OUT" in text else "TEXT"
                    
                    entities.append(FactoryEntity(
                        id=str(e.dxf.handle),
                        name=text,
                        type=entity_type,
                        position=Vector3(x, y)
                    ))
            except Exception as err:
                log.warning(f"Skipping entity: {err}")

        # Calculate Scene Metadata
        width = max_x - min_x if max_x > min_x else 10000
        height = max_y - min_y if max_y > min_y else 10000
        center = Vector3(min_x + width/2, min_y + height/2)

        log.info(f"Extracted {len(entities)} entities, {len(production_lines)} connections. Floor: {width:.0f}x{height:.0f}")
        return FactoryLayout(str(filepath), width, height, center, entities, production_lines)
