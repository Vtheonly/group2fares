import os
import requests
from pathlib import Path
from factory_builder.utils import get_logger

log = get_logger("CloudRenderer")

class CloudRenderer:
    def __init__(self):
        # API Config is pulled from Environment Variables
        self.api_url = os.getenv("API_URL")
        self.timeout = int(os.getenv("API_TIMEOUT", "1200")) # 20 minutes default

    def generate(self, image_path: str, output_path: Path) -> bool:
        """
        Uploads image -> Waits for Processing -> Streams GLB to output_path.
        """
        if not self.api_url:
            log.error("API_URL not set in environment (check .env file).")
            return False

        if not os.path.exists(image_path):
            log.error(f"Source image missing: {image_path}")
            return False

        try:
            with open(image_path, 'rb') as f:
                files = {'file': (Path(image_path).name, f, 'image/png')}
                log.info(f"   🚀 Uploading to GPU Backend...")
                
                # POST request with stream=True to handle large binary response
                response = requests.post(
                    self.api_url, 
                    files=files, 
                    stream=True, 
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    # Stream write to disk to save memory
                    with open(output_path, 'wb') as out_f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk: out_f.write(chunk)
                    
                    log.info(f"   ✨ GLB Model Generated & Saved.")
                    return True
                
                else:
                    log.error(f"   ❌ Server Error {response.status_code}: {response.text}")
                    return False

        except requests.exceptions.ConnectionError:
            log.error(f"   ❌ Could not connect to API at {self.api_url}. Is Ngrok running?")
            return False
        except requests.exceptions.Timeout:
            log.error(f"   ❌ Request timed out after {self.timeout}s.")
            return False
        except Exception as e:
            log.error(f"   ❌ Unexpected Error: {e}")
            return False