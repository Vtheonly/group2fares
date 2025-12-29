import time
import requests
import re
from pathlib import Path
from factory_builder.config import Config
from factory_builder.domain import FactoryEntity
from factory_builder.utils import get_logger

log = get_logger("Scraper")

class ImageScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def process_entities(self, entities: list[FactoryEntity]):
        """Iterates through entities and finds images for machines."""
        machines = [e for e in entities if e.type == "MACHINE"]
        log.info(f"Scouting images for {len(machines)} machines...")

        for machine in machines:
            self._find_image(machine)
            time.sleep(1)  # Be nice to Google

    def _find_image(self, entity: FactoryEntity):
        # 1. Check Cache
        save_path = Config.INPUT_DIR / f"{entity.clean_name}.png"
        if save_path.exists():
            entity.image_path = str(save_path)
            return

        # 2. Search Google Images
        query = f"{entity.name} industrial machine"
        log.info(f"Searching Google for: '{query}'")
        
        try:
            urls = self._search_google_images(query)
            for url in urls:
                if self._download(url, save_path):
                    entity.image_path = str(save_path)
                    log.info(f"✅ Found: {entity.name}")
                    return
            
            log.warning(f"❌ No image found for: {entity.name}")
        
        except Exception as e:
            log.error(f"Search failed for {entity.name}: {e}")

    def _search_google_images(self, query: str, max_results: int = 10) -> list[str]:
        """Scrapes Google Images for image URLs."""
        search_url = "https://www.google.com/search"
        params = {
            "q": query,
            "tbm": "isch",  # Image search
            "hl": "en",
        }
        
        resp = self.session.get(search_url, params=params, timeout=10)
        resp.raise_for_status()
        
        # Extract image URLs from the HTML
        # Google embeds image URLs in various formats, this regex catches common patterns
        pattern = r'"(https?://[^"]+\.(?:jpg|jpeg|png|webp))"'
        urls = re.findall(pattern, resp.text, re.IGNORECASE)
        
        # Filter out Google's own assets
        urls = [u for u in urls if "gstatic.com" not in u and "google.com" not in u]
        
        return urls[:max_results]

    def _download(self, url: str, path: Path) -> bool:
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            # Check if we got actual image content
            content_type = resp.headers.get("Content-Type", "")
            if "image" not in content_type and len(resp.content) < 1000:
                return False
            with open(path, "wb") as f:
                f.write(resp.content)
            return True
        except Exception:
            return False
