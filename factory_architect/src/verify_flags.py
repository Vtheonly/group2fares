import ezdxf
import os
import sys

def read_dxf_flags(dxf_path):
    if not os.path.exists(dxf_path):
        print(f"Error: File not found at {dxf_path}")
        return

    try:
        doc = ezdxf.readfile(dxf_path)
    except IOError:
        print(f"Error: Not a DXF file or a generic I/O error.")
        return
    except ezdxf.DXFStructureError:
        print(f"Error: Invalid or corrupted DXF file.")
        return

    print(f"\n--- Scanning XDATA in {os.path.basename(dxf_path)} ---\n")
    
    msp = doc.modelspace()
    
    # 1. Scan Machines (Block References)
    print(">>> MACHINES (Block References)")
    machine_count = 0
    for entity in msp.query('INSERT'):
        if entity.has_xdata("FACTORY_ARCHITECT"):
            xdata = entity.get_xdata("FACTORY_ARCHITECT")
            print(f"  [Found Machine]")
            # xdata is a list of (group_code, value) tuples
            for code, value in xdata:
                if code == 1000: # String data
                    print(f"    - {value}")
            machine_count += 1
    
    if machine_count == 0:
        print("  No machines with flags found.")

    # 2. Scan Production Lines (Polylines)
    print("\n>>> PRODUCTION LINES (Polylines)")
    line_count = 0
    for entity in msp.query('LWPOLYLINE'):
        if entity.has_xdata("FACTORY_ARCHITECT"):
            xdata = entity.get_xdata("FACTORY_ARCHITECT")
            print(f"  [Found Connection]")
            for code, value in xdata:
                if code == 1000:
                    print(f"    - {value}")
            line_count += 1

    if line_count == 0:
        print("  No production lines with flags found.")
    
    print(f"\nTotal: {machine_count} Machines, {line_count} Connections verified.")

if __name__ == "__main__":
    # Default to the known output path if no arg provided
    default_path = "factory_architect/data/output/Tesla_Battery_Line_C_Advanced.dxf"
    target = sys.argv[1] if len(sys.argv) > 1 else default_path
    
    read_dxf_flags(target)
