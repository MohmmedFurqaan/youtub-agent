import os
import time
import pathlib
import logging
import sys
from pathlib import Path

def setup_logging(name: str = __name__) -> logging.Logger:
    """
    Configure and set up logging for the application.
    
    Args:
        name (str): The name for the logger, defaults to the module name
        
    Returns:
        logging.Logger: Configured logger instance
    """

    # Reconfigure stdout to use UTF-8 to handle the emojis sent by the user
    sys.stdout.reconfigure(encoding='utf-8')

    # Get project root directory
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    log_base = os.path.join(project_root, 'logs')
    
    # Create logs directory if it doesn't exist
    pathlib.Path(log_base).mkdir(parents=True, exist_ok=True)
    
    # Create log file with current date types 
    current_date = time.strftime('%Y-%m-%d')
    file_path = os.path.join(log_base, f'agent_{current_date}.log')
    
    # Set up logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # File handler
    file_handler = logging.FileHandler(file_path, encoding='utf-8')
    formatter = logging.Formatter(
        fmt='%(asctime)s:%(levelname)s:%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    formatter.converter = time.gmtime
    file_handler.setFormatter(formatter)
    
    # Stream handler for console output
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    
    # Add handlers if they haven't been added already
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
    
    return logger
