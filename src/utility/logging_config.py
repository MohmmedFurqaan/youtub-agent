import os
import time
import pathlib
import logging
import sys
from pathlib import Path

from src.utility.file_manipuator import FileManipulator

def setup_logging(name: str = __name__) -> logging.Logger:
    """
    Configure and set up logging for the application.
    
    Args:
        name (str): The name for the logger, defaults to the module name
        
    Returns:
        logging.Logger: Configured logger instance
    """

    # Reconfigure stdout to use UTF-8 to handle the emojis sent by the user
    # pyrefly: ignore [missing-attribute]
    sys.stdout.reconfigure(encoding='utf-8')

    # Get project root directory & ensure logs directory exists
    project_root = FileManipulator.get_project_root()
    log_base = FileManipulator.ensure_dir(project_root / 'logs')
    
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
