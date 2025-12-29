import logging
import sys

def get_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('cols="%(asctime)s" level=%(levelname)s module=%(name)s msg="%(message)s"')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger
