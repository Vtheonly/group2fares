import requests
import re
from pathlib import Path
from factory_builder.utils import get_logger

log = get_logger("Scraper")

class ImageScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def find_and_save(self, query: str, output_path: Path) -> bool:
        """
        Scrapes an image for 'query' and saves it to 'output_path'.
        Returns True if successful, False otherwise.
        """
        # Augment query for better industrial results
        search_query = f"{query} industrial machine equipment white background"
        
        try:
            urls = self._search_google_images(search_query)
            if not urls:
                log.warning(f"No URLs found for: {query}")
                return False

            for url in urls:
                if self._download(url, output_path):
                    return True
            
            return False

        except Exception as e:
            log.error(f"Scraping error for '{query}': {e}")
            return False

    def _search_google_images(self, query: str) -> list[str]:
        """Parses Google Images results for direct image links."""
        url = "https://www.google.com/search"
        params = {
            "q": query,
            "tbm": "isch",  # Image search mode
            "hl": "en",
        }
        
        try:
            res = self.session.get(url, params=params, timeout=10)
            res.raise_for_status()
            
            # Regex to find image URLs (heuristic)
            # Looks for common image extensions in JSON blobs or HTML attributes
            pattern = r'"(https?://[^"]+\.(?:jpg|jpeg|png|webp))"'
            urls = re.findall(pattern, res.text, re.IGNORECASE)
            
            # Filter out internal Google thumbnails or tracking links
            clean_urls = [u for u in urls if "gstatic.com" not in u and "google.com" not in u]
            return clean_urls[:8] # Return top 8 candidates

        except Exception as e:
            log.error(f"Search failed: {e}")
            return []

    def _download(self, url: str, path: Path) -> bool:
        """Attempts to download the image from the URL."""
        try:
            res = self.session.get(url, timeout=10)
            if res.status_code == 200:
                # Basic validation: ensure it's actually an image
                if "image" not in res.headers.get("Content-Type", "") and len(res.content) < 1000:
                    return False
                
                with open(path, "wb") as f:
                    f.write(res.content)
                return True
        except Exception:
            pass
        return False