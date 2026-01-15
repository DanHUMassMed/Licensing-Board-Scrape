#!/usr/bin/env python3
"""
download_minutes.py

Download Boston Voting Minutes PDFs into a common directory.
"""

import os
import requests
from urllib.parse import urljoin
from pathlib import Path
import json
from pathlib import Path
import shutil
import hashlib
import pikepdf
from io import BytesIO


BASE_URL = "https://www.boston.gov"
DOWNLOAD_DIR = Path("./voting_minutes_pdfs")
EXCEPTION_PDFS = "./data/exception_pdfs"
VOTING_MINUTES_LINKS = "./data/voting_minutes_links.json"
URL_EXCLUDE_LIST = "./data/url_exclude_list.json"
DOWNLOAD_DIR.mkdir(exist_ok=True)


def read_data(json_path):
    """
    Reads the list of links with 'href', 'body', 'date' from a JSON file.

    Args:
        json_path (str or Path): Path to the JSON file

    Returns:
        list: List of dictionaries with 'href', 'body', 'date'
    """
    json_file = Path(json_path)
    if not json_file.exists():
        raise FileNotFoundError(f"JSON file not found: {json_file}")

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Optional: validate data format
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of links in JSON, got {type(data)}")

    for i, item in enumerate(data):
        if not all(key in item for key in ("href", "body", "date")):
            raise ValueError(f"Item {i} is missing required keys: {item}")

    return data

def _is_google_drive_url(url: str) -> bool:
    return "drive.google.com/file" in url

def _google_drive_to_download_url(url: str) -> str:
    """
    Convert a Google Drive file URL to a direct download (PDF) URL.
    """
    marker = "/file/d/"
    if marker not in url:
        return url

    file_id = url.split(marker, 1)[1].split("/", 1)[0]

    return f"https://drive.google.com/uc?export=download&id={file_id}"



def append_to_url_exclude_list(new_url: str, file_path: str = URL_EXCLUDE_LIST):
    """
    Appends a URL to the JSON exclude list if it is not already present.

    Args:
        new_url (str): The URL to append
        file_path (str): Path to the JSON file
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Load existing list or start fresh
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                url_list = json.load(f)
                if not isinstance(url_list, list):
                    print(f"Warning: {file_path} does not contain a list. Resetting to empty list.")
                    url_list = []
            except json.JSONDecodeError:
                print(f"Warning: {file_path} is not valid JSON. Resetting to empty list.")
                url_list = []
    else:
        url_list = []

    # Append only if not already present
    if new_url not in url_list:
        url_list.append(new_url)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(url_list, f, indent=4)
        print(f"Added URL to exclude list: {new_url}")
    else:
        print(f"URL already in exclude list: {new_url}")


def pull_data(href):
    """
    Downloads the content from BASE_URL + href and confirms it is a valid PDF.

    Args:
        href (str): The relative URL of the file

    Returns:
        bytes: The file content if it is a valid PDF, else None
    """
    if _is_google_drive_url(href):
        href = _google_drive_to_download_url(href)

    url = urljoin(BASE_URL, href)
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        content = response.content

        # Validate PDF using BytesIO
        try:
            with pikepdf.open(BytesIO(content)):
                pass  # PDF is valid
        except pikepdf.PdfError:
            append_to_url_exclude_list(href)
            return None

        return content

    except requests.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None



def save_data(file_content: bytes, date_str: str):
    """
    Save file_content to DOWNLOAD_DIR only if content differs.
    Avoids creating versioned files for identical content.
    """
    base_name = f"voting_minutes_{date_str}.pdf"
    base_path = DOWNLOAD_DIR / base_name

    incoming_hash = hashlib.sha256(file_content).digest()

    def file_hash(path, chunk_size=1024 * 1024):
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                h.update(chunk)
        return h.digest()

    # Case 1: base file exists — check if identical
    if base_path.exists():
        if file_hash(base_path) == incoming_hash:
            print(f"No change detected — {base_path.name} already up to date")
            return base_path

    # Case 2: check versioned files
    index = 1
    while True:
        candidate = (
            base_path if index == 1
            else DOWNLOAD_DIR / f"voting_minutes_{date_str}_v{index}.pdf"
        )

        if not candidate.exists():
            with candidate.open("wb") as f:
                f.write(file_content)
            print(f"Saved {candidate.name}")
            return candidate

        if file_hash(candidate) == incoming_hash:
            print(f"Duplicate content detected — matches {candidate.name}")
            return candidate

        index += 1


def pdf_exceptions():
    """
    Copy all PDF files from EXCEPTION_PDFS directory into DOWNLOAD_DIR.
    """
    src_dir = Path(EXCEPTION_PDFS)
    download_dir = Path(DOWNLOAD_DIR)

    if not src_dir.exists():
        return

    download_dir.mkdir(parents=True, exist_ok=True)

    for pdf in src_dir.glob("*.pdf"):
        shutil.copy2(pdf, download_dir / pdf.name)

def main():
    links_list = read_data(VOTING_MINUTES_LINKS)

    for item in links_list:
        href = item.get("href")
        date = item.get("date")
        if not href or not date:
            print(f"Skipping item (missing href or date): {item}")
            continue

        content = pull_data(href)
        if content:
            save_data(content, date)
        else:
            print(f"Failed to download: {href}")

    pdf_exceptions()

if __name__ == "__main__":
    main()
