"""
Centralized Logger Configuration
Single logging setup for entire codebase
"""
import logging
import sys
from pathlib import Path

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Global flag to prevent multiple configurations
_logging_configured = False


def setup_logging(log_level=logging.INFO, log_file="app.log"):
    """
    Setup centralized logging configuration for entire application
    
    Args:
        log_level: Logging level (default: INFO)
        log_file: Name of log file (default: app.log)
    """
    global _logging_configured
    
    if _logging_configured:
        return
    
    # Suppress noisy third-party loggers
    logging.getLogger('faiss').setLevel(logging.WARNING)
    logging.getLogger('faiss.loader').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('google').setLevel(logging.ERROR)
    logging.getLogger('google.rpc').setLevel(logging.ERROR)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOGS_DIR / log_file, mode='a')
        ],
        force=True  # Override any existing configuration
    )
    
    _logging_configured = True


def get_logger(name):
    """
    Get a logger instance with the given name
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    # Ensure logging is configured
    if not _logging_configured:
        setup_logging()
    
    return logging.getLogger(name)


# Setup logging on module import
setup_logging()
