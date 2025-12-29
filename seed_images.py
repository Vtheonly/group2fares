from pathlib import Path
import shutil
import re
import sys

# Script to pre-seed PNG images into the NEW strict input directory
# This simulates a successful "Phase 1: Batch Scrape" with PNGs

# Host path maps to /app/factory_builder/input
INPUT_DIR = Path('factory_builder/input')
INPUT_DIR.mkdir(parents=True, exist_ok=True)

# Source for placeholder image (using a known existing PNG)
SOURCE_IMG = Path('factory_builder/venv/lib/python3.12/site-packages/ezdxf/resources/64x64.png')

if not SOURCE_IMG.exists():
    print(f"Error: Source image not found at {SOURCE_IMG}")
    # Try finding any png
    import glob
    pngs = glob.glob("**/*.png", recursive=True)
    if pngs:
        SOURCE_IMG = Path(pngs[0])
        print(f"Fallback source: {SOURCE_IMG}")
    else:
        print("No PNG found to use as seed.")
        sys.exit(1)

def sanitize_name(name: str) -> str:
    """Convert machine name to filesystem-safe name."""
    safe = re.sub(r'[^\w\s-]', '_', name)
    safe = re.sub(r'\s+', '_', safe)
    safe = re.sub(r'_+', '_', safe)
    return safe.strip('_')

# List of machines from "ALLO MAISON" factory (exact names from input.json)
machines = [
    "High-Speed Mixer (PVC/Stone Powder)",
    "Twin-Screw Extruder & Die Head",
    "4-Roll Calender & Lamination Unit",
    "Multi-Zone Cooling Rack & Haul-Off",
    "Automatic Cross Cutter & Trimmer",
    "Double-End Tenoner (Click System)",
    "Automated Stacking & Packaging System"
]

print(f"Seeding PNG images to: {INPUT_DIR}")
print(f"Source: {SOURCE_IMG}")

for machine in machines:
    safe_name = sanitize_name(machine)
    target = INPUT_DIR / f"{safe_name}.png"
    shutil.copy(SOURCE_IMG, target)
    print(f"✓ Seeded: {target}")

print("Done.")
