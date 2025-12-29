import time
import requests
from duckduckgo_search import DDGS
from pathlib import Path
from factory_builder.config import Config
from factory_builder.domain import FactoryEntity
from factory_builder.utils import get_logger

log = get_logger("Scraper")

class ImageScraper:
    def __init__(self):
        self.session = DDGS()

    def process_entities(self, entities: list[FactoryEntity]):
        """Iterates through entities and finds images for machines."""
        machines = [e for e in entities if e.type == "MACHINE"]
        log.info(f"Scouting images for {len(machines)} machines...")

        for machine in machines:
            self._find_image(machine)

    def _find_image(self, entity: FactoryEntity):
        # 1. Check Cache (in input folder for cloud upload)
        save_path = Config.INPUT_DIR / f"{entity.clean_name}.jpg"
        if save_path.exists():
            entity.image_path = str(save_path)
            return

        # 2. Search
        query = f"{entity.name} industrial machine isolated white background product shot"
        try:
            results = self.session.images(query, max_results=3)
            for res in results:
                url = res.get('image')
                if url and self._download(url, save_path):
                    entity.image_path = str(save_path)
                    log.info(f"✅ Found: {entity.name}")
                    return
            
            log.warning(f"❌ No image found for: {entity.name}")
        
        except Exception as e:
            log.error(f"Search failed for {entity.name}: {e}")
            time.sleep(2) # Backoff

    def _download(self, url: str, path: Path) -> bool:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            with open(path, "wb") as f:
                f.write(resp.content)
            return True
        except Exception:
            return False
