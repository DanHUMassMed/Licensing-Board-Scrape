# Code Review - 01-15-2026

## Overview

This review covers the following Python scripts in the `src/` directory:
- `scrape_licensing_board.py`
- `download_minutes.py`
- `extract_pdf_text.py`

The review evaluates adherence to SOLID principles, Python best practices, and overall code quality.

## General Observations

- **Logging**: Excellent use of the `logging` module across all scripts instead of `print` statements. This improves observability and debugging.
- **Type Hinting**: Partial use of type hints is present, which is good, but could be more consistent.
- **Error Handling**: `try-except` blocks are used for network requests and file operations, which makes the scripts robust.
- **Project Structure**: separation of concerns into distinct scripts (scraping links, downloading files, extracting text) is a strong architectural choice that naturally supports the Single Responsibility Principle.

---

## SOLID Principles Analysis

### 1. Single Responsibility Principle (SRP)

**Observation:**
The separation of the pipeline into three distinct scripts (`scrape`, `download`, `extract`) is a great example of SRP at the macro level.
- `scrape_licensing_board.py`: Responsible for fetching the webpage and parsing metadata.
- `download_minutes.py`: Responsible for retrieving binary content.
- `extract_pdf_text.py`: Responsible for transformation (PDF -> Text).

**Critique - `scrape_licensing_board.py`:**
This script is doing slightly too much. It:
1. Fetches HTML.
2. Parses HTML.
3. Cleans/filters data.
4. Extracts regular links AND video links.
5. Saves JSON files.
6. Logs stats to CSV.

*Recommendation*: Consider moving the CSV logging and JSON saving into separate utility functions or a `DataManager` class. The regex parsing logic for dates (`extract_date`) is complex enough to warrant its own module or helper class.

### 2. Open/Closed Principle (OCP)

**Observation:**
The filtering logic (`remove_client_side_links`, `remove_exclude_links`) works well but is hardcoded. If we wanted to add a new type of filter (e.g., "remove links containing 'facebook'"), we would have to modify the source code.

*Recommendation*: Implement a filter interface or use a list of callable filter functions. This would allow adding new filters without modifying the main parsing logic.

### 3. Liskov Substitution Principle (LSP)

**Observation:**
Not heavily applicable here as there isn't deep class inheritance. The scripts are primarily procedural.

### 4. Interface Segregation Principle (ISP)

**Observation:**
The functions generally have small, specific signatures (e.g., `pull_data(href)`), which is good.

### 5. Dependency Inversion Principle (DIP)

**Observation:**
The scripts rely heavily on concrete implementations (e.g., `requests.get`, `open(file, 'w')`).
- `download_minutes.py` imports `requests` directly.

*Recommendation*: For a more robust production system, one might inject a "Downloader" dependency. This would allow mocking the network layer easily for unit tests without making real HTTP calls.

---

## Python Best Practices & Specific Feedback

### 1. Global State & Constants
**File:** All files
**Issue:** Paths like `LOG_DIR = Path("log")` and configuration paths are defined at the module level.
**Improvement:** Move configuration into a `Config` class or load from a `.env` / `config.toml` file. This prevents path issues when running scripts from different directories.

### 2. Logging Configuration Duplication
**File:** All files
**Issue:** Every script re-implements the logging setup code.
```python
logging.basicConfig(
    level=logging.INFO,
    ...
)
```
**Improvement:** Create a shared module (e.g., `src/logger.py`) that exports a `get_logger()` function or `setup_logging()` function. This ensures consistent formatting and log file location across the entire project (DRY Principle).

### 3. Date Parsing Complexity
**File:** `scrape_licensing_board.py`
**Function:** `extract_date`
**Issue:** The function relies on multiple nested fallback strategies and regexes. It is long and hard to read.
**Improvement:** Refactor into a `DateParser` class with clearly named methods for each strategy (`_parse_from_body`, `_parse_from_href_numeric`, etc.).

### 4. Hardcoded Paths
**File:** `scrape_licensing_board.py`
**Issue:**
```python
VIDEO_LINKS_FILE = "data/hearing_video_links.json"
```
**Improvement:** Use `pathlib.Path` consistently for all file references. While `Path` is imported, strings are still often used for file paths until the moment they are used.

### 5. Exception Handling Granularity
**File:** `download_minutes.py`
**Function:** `pull_data`
**Issue:**
```python
except requests.RequestException as e:
    logger.error(f"Error downloading {url}: {e}")
    return None
```
**Improvement:** This swallows the error and returns `None`. While this keeps the script running, it might verify that `None` is handled correctly everywhere up the stack. It appears `save_data` is skipped if content is `None`, which is correct.

### 6. Variable Naming
**File:** `scrape_licensing_board.py`
**Issue:** `links_list` is a bit generic.
**Improvement:** Use more semantic names like `scraped_items` or `minute_candidates`.

### 7. Google Drive Logic
**File:** `download_minutes.py`
**Observation:** The Google Drive extraction logic (`_google_drive_to_download_url`) is a brittle/custom workaround.
**Improvement:** This is often necessary for scrapers, but consider moving provider-specific logic (YouTube, Google Drive) into a separate `providers.py` module to keep the clean business logic separated from the messy vendor integration details.

## Summary of Actionable Items

1.  **Refactor Logging**: Extract logging setup to `src/utils/logger.py`.
2.  **Refactor Parsing**: Move date parsing regexes to `src/parsers/date_parser.py`.
3.  **Config Management**: Centralize file paths and constants.
4.  **Type Hints**: Add return type annotations to all functions (e.g., `-> List[Dict[str, Any]]:`).

## Conclusion

The code is functional, modular, and easy to read. It follows the spirit of SRP well by splitting tasks into scripts. The main areas for improvement are reducing code duplication (logging config) and better organizing complex logic (date parsing) into dedicated classes/modules.
