import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote
import json
import os
import re
import sys
from datetime import datetime
import csv

# Constants
TARGET_URL = "https://www.boston.gov/departments/licensing-board/licensing-board-information-and-members"
VIDEO_LINKS_FILE = "data/hearing_video_links.json"
MINUTES_LINKS_FILE = "data/voting_minutes_links.json"
URL_EXCLUDE_LIST_FILE = "data/url_exclude_list.json"
STATS_LOG_FILE = "data/link_stats_log.csv"


def get_html_content(url, timeout=10):
    """
    Fetches the HTML content from the given URL.

    Args:
        url (str): URL to fetch HTML content from.
        timeout (int): Request timeout in seconds.

    Returns:
        str: HTML content as a string.

    Raises:
        RuntimeError: If the request fails or returns a non-200 status code.
    """
    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as e:
        raise RuntimeError(f"Network error while fetching {url}") from e

    if response.status_code != 200:
        raise RuntimeError(
            f"Unexpected status code {response.status_code} for {url}"
        )

    if not response.text:
        raise RuntimeError(f"Empty response body for {url}")

    return response.text


def get_href_tags(html_content):
    """
    Parses HTML content and returns a list of dictionaries containing
    href and body text for all <a> tags.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    links_data = []
    
    # process all links
    links = soup.find_all('a', href=True)
    
    for link in links:
        href = link['href']
        body = link.get_text(strip=True)
        links_data.append({"href": href, "body": body})
        
    return links_data

def remove_client_side_links(links_list):
    """
    Removes client side references (tel:, mailto:, #, etc.) from the links list.
    
    Args:
        links_list (list): List of dictionaries with 'href' and 'body'.
        
    Returns:
        list: Filtered list of dictionaries.
    """
    cleaned_links = []
    local_prefixes = ('tel:', 'mailto:', '#', 'javascript:')
    
    for link in links_list:
        href = link.get('href', '').lower()
        if not href.startswith(local_prefixes):
            cleaned_links.append(link)
            
    return cleaned_links

import os
import json

def remove_exclude_links(links_list, exclude_file=URL_EXCLUDE_LIST_FILE):
    """
    Removes links whose href matches an entry in the exclude list.

    Args:
        links_list (list): List of dictionaries with 'href' and 'body'.
        exclude_file (str): Path to the exclude list JSON file.

    Returns:
        list: Filtered list of dictionaries.

    Raises:
        FileNotFoundError: If the exclude file does not exist.
        ValueError: If the exclude file contains invalid JSON.
    """
    if not os.path.exists(exclude_file):
        raise FileNotFoundError(f"Exclude file not found: {exclude_file}")

    try:
        with open(exclude_file, 'r', encoding='utf-8') as f:
            exclude_list = set(json.load(f))
    except json.JSONDecodeError as e:
        raise ValueError(f"Exclude file is corrupted: {exclude_file}") from e

    return [
        link for link in links_list
        if link.get("href", "") not in exclude_list
    ]


def _is_youtube_url(url: str) -> bool:
    if not isinstance(url, str):
        return False

    url = url.lower()

    return (
        "youtube.com" in url
        or "youtu.be" in url
        or "youtube" in url
    )

def extract_hearing_video_links(links_list):
    """
    Separates links into video links and other links.
    
    Args:
        links_list (list): List of dictionaries with 'href' and 'body'.
        
    Returns:
        tuple: (video_links, minutes_links) where each is a list of dictionaries.
    """
    video_links = []
    minutes_links = []
    
    for link in links_list:
        href = link.get('href', '')
        if _is_youtube_url(href):
            video_links.append(link)
        else:
            minutes_links.append(link)
            
    return video_links, minutes_links


# Regex patterns
BODY_MONTH_DAY_PATTERN = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December)[\s,]+(\d{1,2})(?:st|nd|rd|th)?(?:,\s*(\d{4}))?",
    re.IGNORECASE
)

HREF_NUMERIC_PATTERN = re.compile(r"(\d{1,2})-(\d{1,2})-(\d{2,4})")
HREF_MONTH_PATTERN = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December)[^\d]*(\d{1,2})[^\d]*(\d{4})",
    re.IGNORECASE
)

MONTH_NAME_TO_NUM = {datetime(2000, i, 1).strftime("%B"): i for i in range(1, 13)}


def extract_date(links_list):
    """
    Adds 'date' field (YYYY-MM-DD) to each link dict if a date can be found.
    Checks body first, then href (numeric or month name). Skips entries if no date.
    If year is missing, uses 'yyyy' placeholder.
    """
    result = []

    for item in links_list:
        date_obj = None
        year_str = None
        month_str = None
        day_str = None

        body = item.get("body", "")
        href = item.get("href", "")
        href_decoded = unquote(href)

        # 1️⃣ Try to parse from body
        body_match = BODY_MONTH_DAY_PATTERN.search(body)
        if body_match:
            month_name, day, year = body_match.groups()
            day_str = f"{int(day):02d}" if day else None
            month_str = f"{MONTH_NAME_TO_NUM[month_name.capitalize()]:02d}" if month_name else None
            year_str = year if year else None

        # 2️⃣ Fallback: numeric mm-dd-yy in href
        if not month_str or not day_str or not year_str:
            num_match = HREF_NUMERIC_PATTERN.search(href_decoded)
            if num_match:
                m, d, y = num_match.groups()
                month_str = month_str or f"{int(m):02d}"
                day_str = day_str or f"{int(d):02d}"
                if y:
                    y_int = int(y)
                    if y_int < 100:
                        y_int += 2000
                    year_str = year_str or str(y_int)

        # 3️⃣ Fallback: month name in href
        if not month_str or not day_str or not year_str:
            month_match = HREF_MONTH_PATTERN.search(href_decoded)
            if month_match:
                month_name, day, year = month_match.groups()
                month_str = month_str or f"{MONTH_NAME_TO_NUM[month_name.capitalize()]:02d}"
                day_str = day_str or f"{int(day):02d}"
                year_str = year_str or year

        # Compose final date string with placeholders if missing
        final_year = year_str if year_str else "yyyy"
        final_month = month_str if month_str else "mm"
        final_day = day_str if day_str else "dd"
        date_str = f"{final_year}-{final_month}-{final_day}"

        # Add date to item
        new_item = item.copy()
        new_item["date"] = date_str
        result.append(new_item)

    return result

def log_link_stats_csv(
    link_stats: dict,
    csv_path: str = STATS_LOG_FILE,
    run_date: str | None = None,
):
    """
    Appends link statistics for a scraper run to a CSV file.

    Args:
        link_stats (dict): Dictionary containing link counts.
        csv_path (str): Path to the CSV log file.
        run_date (str | None): Optional run date (YYYY-MM-DD).
                               Defaults to today's date.
    """
    if run_date is None:
        run_date = datetime.now().strftime("%Y-%m-%d")

    # Enforce stable column order
    fieldnames = [
        "run_date",
        "total_links",
        "client_side_links",
        "excluded_links",
        "video_links",
        "minutes_links",
    ]

    row = {"run_date": run_date}
    row.update({k: link_stats.get(k, 0) for k in fieldnames if k != "run_date"})

    file_exists = os.path.exists(csv_path)

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        # Write header once
        if not file_exists:
            writer.writeheader()

        writer.writerow(row)

def main():
    print(f"Fetching {TARGET_URL}...")
    link_stats = {
        "total_links": 0,
        "client_side_links": 0,
        "excluded_links": 0,
        "video_links": 0,
        "minutes_links": 0,
    }
    try:
        html_content = get_html_content(TARGET_URL)

        print("Parsing links...")
        links_list = get_href_tags(html_content)
        link_stats["total_links"] = len(links_list)

        # Remove client side links
        print("Removing client side links...")
        links_list = remove_client_side_links(links_list)
        link_stats["client_side_links"] = link_stats["total_links"] - len(links_list)
        
        # Remove excluded links
        print("Removing excluded links...")
        links_list = remove_exclude_links(links_list)
        link_stats["excluded_links"] = link_stats["total_links"] - link_stats["client_side_links"] - len(links_list)
        
        # Separate videos from minutes
        print("Separating video links...")
        video_links, minutes_links = extract_hearing_video_links(links_list)
        link_stats["video_links"] = len(video_links)
        link_stats["minutes_links"] = len(minutes_links)
        
        # Save video links
        print(f"Saving video links to {VIDEO_LINKS_FILE}...")
        with open(VIDEO_LINKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(video_links, f, indent=4)
    
        # Add date to minutes links
        minutes_links = extract_date(minutes_links)
        
        # Save minutes links
        print(f"Saving voting minutes links to {MINUTES_LINKS_FILE}...")
        with open(MINUTES_LINKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(minutes_links, f, indent=4)

        # Stats
        print("Link stats:")
        for key, value in link_stats.items():
            print(f"{key}: {value}")

        log_link_stats_csv(link_stats)
    except FileNotFoundError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Invalid exclude file: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"❌ Network error: {e}")
        sys.exit(1)
        
    print("Done.")

if __name__ == "__main__":
    main()
