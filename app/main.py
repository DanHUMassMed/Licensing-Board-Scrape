import sys
import logging
from app.config.logger import setup_logging
from app.config import settings
from app.services.scraper import ScraperService
from app.services.downloader import DownloaderService
from app.services.text_extractor import TextExtractorService
from app.link_filters.video_link_separator import VideoLinkSeparator
from app.link_filters.client_side_filter import ClientSideFilter
from app.link_filters.exclude_list_filter import ExcludeListFilter

def main():
    logger = setup_logging(__name__)
    logger.info("Starting Licensing Board Scraper Application")
    
    # 1. Run Scraper
    logger.info("Initializing Scraper Service...")
    scraper = ScraperService()
    
    # Configure Filters
    scraper.add_filter(ClientSideFilter())
    scraper.add_filter(ExcludeListFilter(settings.URL_EXCLUDE_LIST_FILE))
    
    # Execute
    scraper.run()
    
    # 2. Run Downloader
    logger.info("Initializing Downloader Service...")
    downloader = DownloaderService()
    downloader.run()

    # 3. Run Text Extractor
    logger.info("Initializing Text Extractor Service...")
    extractor = TextExtractorService()
    extractor.run()
    
    logger.info("Application finished successfully.")

if __name__ == "__main__":
    main()
