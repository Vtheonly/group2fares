import ezdxf
from ezdxf.layouts import Modelspace
from ezdxf import zoom
from loguru import logger
from src.models.schema import LayoutSchema, PlacedMachine

class DXFRenderer:
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.doc = ezdxf.new("R2010")
        self.msp = self.doc.modelspace()
        self._setup_environment()

    def _setup_environment(self):
        """Setup Layers and Linetypes"""
        # Layers
        layers = [
            ("FACTORY_BOUNDS", 7),    # White
            ("MACHINES", 4),          # Cyan
            ("MACHINES_TEXT", 2),     # Yellow
            ("FLOW_CONVEYOR", 1),     # Red
            ("FLOW_PIPING", 3),       # Green
            ("FLOW_AGV", 6),          # Magenta
            ("ANNOTATIONS", 7)
        ]
        for name, color in layers:
            self.doc.layers.new(name=name, dxfattribs={'color': color})

        # Linetypes
        if "PHANTOM" not in self.doc.linetypes:
            self.doc.linetypes.new('PHANTOM', dxfattribs={'description': 'Phantom', 'pattern': [30.0, 1.25, -0.25, 0.25, -0.25]})
        if "DASHED" not in self.doc.linetypes:
            self.doc.linetypes.new('DASHED', dxfattribs={'description': 'Dashed', 'pattern': [10.0, 5.0]})

    def _get_layer_for_type(self, conn_type: str) -> str:
        """Map connection types to layers"""
        ct = conn_type.lower()
        if "pipe" in ct or "pump" in ct:
            return "FLOW_PIPING"
        if "agv" in ct:
            return "FLOW_AGV"
        return "FLOW_CONVEYOR"

    def _create_machine_block(self, machine: PlacedMachine):
        block_name = f"BLK_{machine.id}"
        if block_name in self.doc.blocks:
            return block_name

        block = self.doc.blocks.new(name=block_name)
        w, l = machine.dimensions.width, machine.dimensions.length
        
        # Geometry
        points = [(-l/2, -w/2), (l/2, -w/2), (l/2, w/2), (-l/2, w/2), (-l/2, -w/2)]
        block.add_lwpolyline(points, dxfattribs={'layer': 'MACHINES', 'lineweight': 35})
        
        # Orientation Marker (Arrow indicating 'Front')
        block.add_lwpolyline([(0, 0), (l/2, 0)], dxfattribs={'layer': 'MACHINES'})
        
        # Text Attribute
        att1 = block.add_attdef("NAME", text=machine.name, dxfattribs={'height': 200, 'color': 2, 'layer': 'MACHINES_TEXT', 'halign': 1, 'valign': 1})
        att1.dxf.insert = (0, 0)
        
        att2 = block.add_attdef("ID", text=machine.id, dxfattribs={'height': 100, 'color': 7, 'layer': 'MACHINES_TEXT', 'halign': 1, 'valign': 3})
        att2.dxf.insert = (0, 0)

        return block_name

    def render(self, layout: LayoutSchema):
        logger.info(f"Rendering layout with {len(layout.machines)} machines and {len(layout.flow_connections)} connections.")

        # 1. Room
        self.msp.add_lwpolyline(
            [(0, 0), (layout.room_width, 0), (layout.room_width, layout.room_height), (0, layout.room_height), (0, 0)],
            dxfattribs={'layer': 'FACTORY_BOUNDS', 'lineweight': 50}
        )

        # 2. Machines
        for m in layout.machines:
            blk_name = self._create_machine_block(m)
            insert = self.msp.add_blockref(
                blk_name, 
                (m.position.x, m.position.y), 
                dxfattribs={'rotation': m.rotation, 'layer': 'MACHINES'}
            )
            insert.add_auto_attribs({'NAME': m.name, 'ID': m.id})
            
            # Extended Data for Interoperability
            insert.set_xdata("FACTORY_ARCHITECT", [
                (1000, "TYPE:MACHINE_NODE"),
                (1000, f"ID:{m.id}"),
                (1000, f"NAME:{m.name}"),
                (1000, f"LENGTH:{m.dimensions.length}"),
                (1000, f"WIDTH:{m.dimensions.width}")
            ])

        # 3. Connections (Edges)
        for flow in layout.flow_connections:
            layer_name = self._get_layer_for_type(flow.connection_type)
            linetype = "DASHED" if "agv" in flow.connection_type.lower() else "CONTINUOUS"
            
            points = [(p.x, p.y) for p in flow.path_points]
            
            # Draw Path
            pline = self.msp.add_lwpolyline(
                points,
                dxfattribs={
                    'layer': layer_name, 
                    'linetype': linetype, 
                    'lineweight': 25
                }
            )

            # Flag the Flow
            pline.set_xdata("FACTORY_ARCHITECT", [
                (1000, "TYPE:CONNECTION_EDGE"),
                (1000, f"FROM:{flow.from_machine_id}"),
                (1000, f"TO:{flow.to_machine_id}"),
                (1000, f"CONN_TYPE:{flow.connection_type}")
            ])

        zoom.extents(self.msp)
        self.doc.saveas(self.output_path)
        logger.success(f"DXF Saved: {self.output_path}")
