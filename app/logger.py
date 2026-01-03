import logging
import os
from config import LOG_LEVEL, TEMP_DIR

# Ensure temp/log directory exists
os.makedirs(TEMP_DIR, exist_ok=True)

# Define log file path
LOG_FILE = os.path.join(TEMP_DIR, "voice_agent.log")

# Configure logger
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger with a consistent configuration across modules.
    """
    return logging.getLogger(name)
