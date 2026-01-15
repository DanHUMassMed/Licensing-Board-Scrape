
class VideoLinkSeparator:
    """Separates video links from other links."""
    
    def process(self, links: list[dict]) -> tuple[list[dict], list[dict]]:
        video_links = []
        other_links = []
        
        for link in links:
            href = link.get('href', '').lower()
            if "youtube.com" in href or "youtu.be" in href:
                video_links.append(link)
            else:
                other_links.append(link)
                
        return video_links, other_links
