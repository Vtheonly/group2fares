import ezdxf
from factory_builder.domain import FactoryLayout, FactoryEntity, Vector3
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
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')

        for e in msp:
            try:
                # 1. Block References (Machines)
                if e.dxftype() == 'INSERT':
                    x, y, _ = e.dxf.insert
                    name = e.dxf.name
                    rotation = getattr(e.dxf, 'rotation', 0)
                    
                    # Track bounds
                    min_x, max_x = min(min_x, x), max(max_x, x)
                    min_y, max_y = min(min_y, y), max(max_y, y)

                    entities.append(FactoryEntity(
                        id=str(e.dxf.handle),
                        name=name,
                        type="MACHINE",
                        position=Vector3(x, y),
                        rotation=rotation
                    ))

                # 2. Text (Labels, Ports)
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
        width = max_x - min_x
        height = max_y - min_y
        center = Vector3(min_x + width/2, min_y + height/2)

        log.info(f"Extracted {len(entities)} entities. Floor: {width:.0f}x{height:.0f}")
        return FactoryLayout(str(filepath), width, height, center, entities)
