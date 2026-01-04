import argparse
import sys
from loguru import logger
from src.services.orchestrator import PipelineOrchestrator

def main():
    parser = argparse.ArgumentParser(description="AI Factory Generator 5.0")
    parser.add_argument(
        "--project", 
        type=str, 
        help="Name of the project folder in factory_architect/data/",
        required=True
    )
    
    args = parser.parse_args()
    
    try:
        orchestrator = PipelineOrchestrator(args.project)
        orchestrator.run()
    except Exception as e:
        logger.critical(f"Pipeline Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()