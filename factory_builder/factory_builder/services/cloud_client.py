import requests
import concurrent.futures
from pathlib import Path
from factory_builder.config import Config
from factory_builder.domain import FactoryEntity
from factory_builder.utils import get_logger

log = get_logger("Cloud_Client")

class CloudRenderer:
    def generate_models(self, entities: list[FactoryEntity]):
        """Sends images to the GPU server in parallel."""
        
        # Only process machines that have images
        tasks = [e for e in entities if e.type == "MACHINE" and e.image_path]
        
        if not tasks:
            log.warning("No machines with images found to render.")
            return

        log.info(f"🚀 Uploading {len(tasks)} machines to Cloud GPU ({Config.API_URL})...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
            future_to_entity = {
                executor.submit(self._upload_and_stream, e): e 
                for e in tasks
            }

            for future in concurrent.futures.as_completed(future_to_entity):
                entity = future_to_entity[future]
                try:
                    result_path = future.result()
                    if result_path:
                        entity.model_path = result_path
                except Exception as exc:
                    log.error(f"Worker failed for {entity.name}: {exc}")

    def _upload_and_stream(self, entity: FactoryEntity) -> str:
        """
        Uploads image -> Waits for GPU -> Streams GLB back to disk.
        Logic matches the 'server-side' behavior of tencent2D3D.ipynb
        """
        # Check Cache
        output_path = Config.MODELS_DIR / f"{entity.clean_name}.glb"
        if output_path.exists():
            return str(output_path)

        try:
            with open(entity.image_path, 'rb') as f:
                files = {'file': (f"{entity.clean_name}.png", f, 'image/png')}
                
                # High timeout because Colab GPU queue handles requests sequentially
                response = requests.post(
                    Config.API_URL, 
                    files=files, 
                    stream=True, 
                    timeout=Config.API_TIMEOUT
                )

                if response.status_code == 200:
                    # Write in chunks to keep memory usage low
                    with open(output_path, 'wb') as f_out:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk: f_out.write(chunk)
                    
                    log.info(f"✨ Generated 3D Model: {entity.name}")
                    return str(output_path)
                else:
                    log.error(f"Server Error {entity.name}: {response.text}")
                    return None

        except requests.exceptions.Timeout:
            log.error(f"Timeout: {entity.name} took too long in queue.")
            return None
        except Exception as e:
            log.error(f"Connection Error {entity.name}: {e}")
            return None
