import requests
import logging
from app.config import settings
from app.parsers.html_parser import HtmlLinkExtractor
from app.parsers.date_parser import DateParser
from app.link_filters.video_link_separator import VideoLinkSeparator
from app.storage.file_manager import JsonIO, StatsLogger

logger = logging.getLogger(__name__)

class ScraperService:
    """Orchestrates the scraping of licensing board links."""

    def __init__(self):
        self.html_parser = HtmlLinkExtractor()
        self.date_parser = DateParser()
        self.json_io = JsonIO()
        self.stats_logger = StatsLogger(settings.STATS_LOG_FILE)
        self.video_separator = VideoLinkSeparator()
        self.filters = []  # List of filters with .process()

    def add_filter(self, filter_obj):
        self.filters.append(filter_obj)

    def run(self):
        logger.info(f"Fetching {settings.TARGET_URL}...")
        try:
            html = self._fetch_html(settings.TARGET_URL)
        except RuntimeError as e:
            logger.critical(str(e))
            return

        logger.info("Parsing links...")
        links = self.html_parser.extract_links(html)
        
        stats = {"total_links": len(links)}
        
        # Apply filters sequentially (e.g. ClientSide, ExcludeList)
        filtered_links = links
        for f in self.filters:
            prev_len = len(filtered_links)
            filtered_links = f.process(filtered_links)
            # Rough logic to attribute stats to the filter class name
            filter_name = f.__class__.__name__
            removed_count = prev_len - len(filtered_links)
            # This mapping mirrors the old script's specific stat keys for compatibility
            if "ClientSide" in filter_name:
                stats["client_side_links"] = removed_count
            elif "Exclude" in filter_name:
                stats["excluded_links"] = removed_count

        # Separate Videos
        logger.info("Separating video links...")
        video_links, minutes_links = self.video_separator.process(filtered_links)
        stats["video_links"] = len(video_links)
        stats["minutes_links"] = len(minutes_links)

        # Process Dates for Minutes
        logger.info("Extracting dates...")
        processed_minutes = []
        for link in minutes_links:
            link['date'] = self.date_parser.parse(link['body'], link['href'])
            processed_minutes.append(link)

        # Save Data
        logger.info(f"Saving {len(video_links)} video links...")
        self.json_io.save(video_links, settings.VIDEO_LINKS_FILE)

        logger.info(f"Saving {len(processed_minutes)} minutes links...")
        self.json_io.save(processed_minutes, settings.MINUTES_LINKS_FILE)

        # Log Stats
        logger.info("Link stats:")
        for k, v in stats.items():
            logger.info(f"{k}: {v}")
        self.stats_logger.log_stats(stats)
        
        logger.info("Scraping completed.")

    def _fetch_html(self, url: str) -> str:
        try:
            resp = requests.get(url, timeout=settings.DEFAULT_TIMEOUT)
            resp.raise_for_status()
            if not resp.text:
                 raise RuntimeError(f"Empty response from {url}")
            return resp.text
        except requests.RequestException as e:
            raise RuntimeError(f"Network error fetching {url}: {e}")
