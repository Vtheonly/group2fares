import http.server
import socketserver
import threading
import os
from pathlib import Path
from loguru import logger

PORT = 8000
# We serve the builder's data folder directly
ROOT_DIR = "/app/factory_builder/data"

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT_DIR, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()
    
    def log_message(self, format, *args):
        # Silence default logs to keep console clean
        pass

class BackgroundAssetServer:
    _instance = None
    _thread = None

    @classmethod
    def start(cls):
        if cls._instance:
            return

        if not os.path.exists(ROOT_DIR):
            logger.warning(f"Asset root {ROOT_DIR} does not exist yet.")
            return

        handler = CORSRequestHandler
        try:
            cls._instance = socketserver.TCPServer(("", PORT), handler)
            cls._thread = threading.Thread(target=cls._instance.serve_forever)
            cls._thread.daemon = True
            cls._thread.start()
            logger.info(f"🚀 Asset Server started on port {PORT} serving {ROOT_DIR}")
        except OSError:
            logger.warning(f"Asset server port {PORT} already in use. Assuming running.")

    @classmethod
    def get_url(cls, project_name: str, relative_path: str) -> str:
        """Generates the localhost URL for the viewer"""
        # browser sees localhost:8000 mapped to container:8000
        # URL structure: http://localhost:8000/<project_name>/scene/factory_complete.glb
        return f"http://localhost:8000/{project_name}/{relative_path}"