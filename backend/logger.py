"""Centralized logging configuration for AgentForge backend."""
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

# Create logs directory if it doesn't exist
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log file name with timestamp
log_filename = LOG_DIR / f"agentforge_{datetime.now().strftime('%Y%m%d')}.log"

# Configure root logger
logger = logging.getLogger("agentforge")
logger.setLevel(logging.DEBUG)

# File handler (DEBUG level - captures everything)
file_handler = logging.handlers.RotatingFileHandler(
    log_filename, maxBytes=10_000_000, backupCount=5
)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
)
file_handler.setFormatter(file_formatter)

# Console handler (INFO level - cleaner output)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
console_handler.setFormatter(console_formatter)

# Add handlers to logger
if not logger.handlers:  # Avoid duplicate handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# Get logger for specific modules
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(f"agentforge.{name}")
