"""
Image scraper client that wraps factory_builder's scraping functionality.
Handles image acquisition for machines with rate limiting and error handling.
"""
import time
import sys
from pathlib import Path
from loguru import logger

# Add factory_builder to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "factory_builder"))

try:
    from factory_builder.services.web_scraper import ImageScraper as BaseImageScraper
    from factory_builder.domain import FactoryEntity, Vector3
except ImportError:
    logger.warning("factory_builder not found in expected location. Scraper will use fallback mode.")
    BaseImageScraper = None


class ScraperClient:
    """
    Client for scraping machine images with proper rate limiting.
    """
    
    def __init__(self, rate_limit_delay: float = 3.0):
        """
        Initialize scraper client.
        
        Args:
            rate_limit_delay: Seconds to wait between searches to avoid rate limiting
        """
        self.rate_limit_delay = rate_limit_delay
        self.scraper = BaseImageScraper() if BaseImageScraper else None
        
    def scrape_machine_image(self, machine_name: str) -> bool:
        """
        Scrape image for a machine and save to factory_builder/input.
        
        Args:
            machine_name: Exact name of the machine
            
        Returns:
            True if image was successfully downloaded, False otherwise
        """
        if not self.scraper:
            logger.error("Image scraper not available.")
            return False
            
        # Use strict input path from factory_builder config
        from factory_builder.config import Config
        from src.core.paths import sanitize_name
        
        safe_name = sanitize_name(machine_name)
        output_path = Config.INPUT_DIR / f"{safe_name}.png"
        
        # Check if already exists
        logger.info(f"Checking for existing image at: {output_path}")
        if output_path.exists():
            logger.info(f"IMAGE FOUND: {output_path}")
            return True
        else:
             logger.warning(f"IMAGE NOT FOUND AT: {output_path}")
            
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create temporary entity
        entity = FactoryEntity(
            id=f"temp_{hash(machine_name)}",
            name=machine_name,
            type="MACHINE",
            position=Vector3(0, 0)
        )
        
        logger.info(f"Scraping image for: {machine_name}")
        
        try:
            # Use scraper's internal method which now respects Config.INPUT_DIR
            self.scraper._find_image(entity)
            
            # Verify download
            if entity.image_path and Path(entity.image_path).exists():
                logger.success(f"✅ Image saved: {entity.image_path}")
                time.sleep(self.rate_limit_delay)
                return True
            else:
                logger.warning(f"❌ No image found for: {machine_name}")
                return False
                
        except Exception as e:
            logger.error(f"Scraping failed for {machine_name}: {e}")
            time.sleep(self.rate_limit_delay)
            return False
    
    def scrape_all_machines(self, machine_names: list[str]) -> dict[str, bool]:
        """
        Scrape images for multiple machines.
        
        Args:
            machine_names: List of machine names
            
        Returns:
            Dict mapping machine name to success status
        """
        results = {}
        
        logger.info(f"Starting image acquisition for {len(machine_names)} machines...")
        
        for i, name in enumerate(machine_names, 1):
            logger.info(f"[{i}/{len(machine_names)}] Processing: {name}")
            # Sequential processing
            results[name] = self.scrape_machine_image(name)
        
        # Summary
        successful = sum(1 for v in results.values() if v)
        logger.info(f"Image acquisition complete: {successful}/{len(machine_names)} successful")
        
        return results
