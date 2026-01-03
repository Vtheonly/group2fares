import os
from pathlib import Path

class Config:
    # --- Paths ---
    # --- Paths ---
    BASE_DIR = Path(os.getcwd())
    # Strict paths as requested by user - matching Docker volume mount at root
    # For local dev, use relative paths
    INPUT_DIR = BASE_DIR / "input"
    OUTPUT_DIR = BASE_DIR / "output"
    CACHE_DIR = BASE_DIR / "cache"
    
    IMAGES_DIR = CACHE_DIR / "images"
    MODELS_DIR = CACHE_DIR / "models"

    # --- Cloud API (Ngrok / Colab) ---
    # Can be overridden via environment variable for Docker
    API_URL = os.getenv(
        "API_URL", 
        "https://prettyish-melanie-aurous.ngrok-free.dev/generate"
    )
    
    # Timeout in seconds (20 mins) to match Colab queue times
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "1200"))
    
    # --- Processing ---
    # Number of concurrent uploads to the Colab queue
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "1"))
    
    # Target size for 3D machines (in mm approx) to normalize scaling
    TARGET_MACHINE_SIZE = float(os.getenv("TARGET_MACHINE_SIZE", "3000.0"))

    @classmethod
    def setup_directories(cls):
        """Ensures all necessary folders exist."""
        for p in [cls.INPUT_DIR, cls.OUTPUT_DIR, cls.IMAGES_DIR, cls.MODELS_DIR]:
            p.mkdir(parents=True, exist_ok=True)
