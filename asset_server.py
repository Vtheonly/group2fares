import http.server
import socketserver
import os

PORT = 8000
DIRECTORY = os.getcwd()  # Serve from the root where this script is run

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

if __name__ == "__main__":
    print(f"📂 Serving files from: {DIRECTORY}")
    print(f"🚀 Asset Server running at http://localhost:{PORT}")
    
    # Ensure static folder exists for the viewer
    if not os.path.exists('static'):
        print("⚠️ Warning: 'static' folder not found in current directory.")

    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        httpd.serve_forever()
