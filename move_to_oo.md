# OO Refactoring Recommendations (Simplified)

## Overview
This document outlines a strategy to refactor the current procedural scripts into a practical Object-Oriented (OO) architecture. The goal is to improve code organization and maintainability by grouping related logic into classes (SRP) and creating a modular structure, **without** adding unnecessary abstraction layers like Abstract Base Classes (ABCs) or complex interfaces.

## Proposed Architecture

We recommend organizing the code into the following package structure. This prioritizes "Grouping by Feature" and "Concrete Implementations".

```
src/
├── config/
│   ├── settings.py       # Centralized constants and paths
│   └── logger.py         # Shared logging configuration
├── parsers/
│   ├── html_parser.py    # Class to extract links from HTML
│   └── date_parser.py    # Class to handle all date parsing logic
├── filters/
│   └── link_filters.py   # Contains concrete filter classes (ExcludeListFilter, ClientSideFilter)
├── storage/
│   ├── file_manager.py   # Handles JSON/CSV IO
│   └── pdf_store.py      # Handles PDF naming and saving
└── services/
    ├── scraper.py        # ScraperService: Orchestrates the scraping flow
    └── downloader.py     # DownloaderService: Orchestrates file downloading
```

---

## Addressing Principles (Practical Approach)

### 1. Single Responsibility Principle (SRP)
**Goal**: Each class should have one job.
**Implementation**: Break the large script into focused helper classes.

*   **`HtmlLinkExtractor`**: Concrete class. Method `extract_links(html)` returns list of dicts.
*   **`DateParser`**: Concrete class. Method `parse_date(text)` returns formatted date string or None.
*   **`JsonStorage`**: Concrete class. Methods `save(data, path)` and `load(path)`.
*   **`ScraperManager`**: The "Business Logic" class. It initializes these helpers and runs the loop.

### 2. Open/Closed Principle (OCP)
**Goal**: Easy to add new filters without rewriting the loop.
**Implementation**: Use Duck Typing or simple callable objects.

Instead of an `ABC`, we just ensure all filters implement a common method like `filter(links)`.

```python
# filters/link_filters.py

class ExcludeListFilter:
    def __init__(self, exclude_file_path):
        self.exclude_items = self._load(exclude_file_path)

    def process(self, links):
         # ... returns filtered list ...
        return [l for l in links if l['href'] not in self.exclude_items]

class ClientSideFilter:
    def process(self, links):
        # ... returns filtered list ...
        return filtered_links

# Service usage
class ScraperService:
    def __init__(self, filters):
        self.filters = filters # List of objects with a .process() method

    def run(self):
        links = ...
        for filter_obj in self.filters:
            links = filter_obj.process(links)
```

### 3. Dependency Management
**Goal**: improved testing and clarity.
**Implementation**: Simple Dependency Injection via cleaning up imports and passing dependencies.

We will not create interfaces like `IHttpClient`. We will simply use `requests` inside a helper method or class. If better mocking is needed later, we can refactor, but for now, direct library usage within dedicated classes is sufficient.

---

## Refactoring Roadmap

### Phase 1: Foundation (Shared Utilities)
1.  **`src/config/logger.py`**: Create a `setup_logging()` function.
2.  **`src/config/settings.py`**: Centralize constants.

### Phase 2: Extract Logic to Classes
3.  **`src/parsers/date_parser.py`**: Create `DateParser` class. Move regexes here.
4.  **`src/filters/link_filters.py`**: Create `ExcludeListFilter`, `ClientSideFilter`, and `VideoLinkSeparator`.

### Phase 3: Service Orchestration
5.  **`src/services/scraper.py`**: Create `ScraperService`.
    *   Constructor takes file paths and config.
    *   `run()` method executes the procedural logic using the helper classes.

### Phase 4: Downloader Refactor
6.  Apply similar grouping to `download_minutes.py`.
    *   `PdfDownloader`: Class to handle fetching bytes, checking Google Drive links, and verifying PDF (pikepdf).
    *   `PdfRepository`: Class to handle checking existing files and saving new ones.

## Benefits
*   **Simplicity**: Easy to read and understand. No "magic" or complex inheritance hierarchies.
*   **Organization**: Code is logically grouped. "Where does date parsing happen?" -> `date_parser.py`.
*   **Maintainability**: Changes are isolated.
