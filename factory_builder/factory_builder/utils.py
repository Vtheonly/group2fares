import logging
import sys
import re

def get_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        # Format: Time - Module - Level - Message
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

def sanitize_filename(name: str) -> str:
    """
    Converts arbitrary strings into filesystem-safe directory names.
    Example: "High-Pressure Pump (Model A)" -> "High_Pressure_Pump_Model_A"
    """
    # Replace non-alphanumeric chars (except hyphens) with underscore
    safe = re.sub(r'[^\w\s-]', '_', name)
    # Replace whitespace with underscore
    safe = re.sub(r'\s+', '_', safe)
    # Remove repetitive underscores
    safe = re.sub(r'_+', '_', safe)
    return safe.strip('_')