import logging
import sys
from pathlib import Path
from app.config.settings import LOG_DIR

def setup_logging(name: str, log_filename: str = "app.log") -> logging.Logger:
    """
    Configures and returns a logger with file and stdout handlers.

    Args:
        name (str): Name of the logger (usually __name__).
        log_filename (str): Name of the log file.

    Returns:
        logging.Logger: Configured logger.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file_path = LOG_DIR / log_filename

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(name)
