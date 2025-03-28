import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"app_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)

logger = logging.getLogger("whatsapp_webhook")

def log_info(message):
    """Log info level message"""
    logger.info(message)

def log_error(message, error=None):
    """Log error with traceback"""
    error_msg = f"{message}"
    if error:
        error_msg += f": {str(error)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
    else:
        logger.error(error_msg)

def log_debug(message):
    """Log debug level message"""
    logger.debug(message)

def log_warning(message):
    """Log warning level message"""
    logger.warning(message) 