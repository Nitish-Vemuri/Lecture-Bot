"""
Logging configuration for LectureBot
"""
import sys
from pathlib import Path
from loguru import logger

from config import LOGS_DIR


def setup_logger():
    """Configure loguru logger with file and console output"""
    
    # Remove default logger
    logger.remove()
    
    # Console output with color
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # File output for all logs
    logger.add(
        LOGS_DIR / "lecturebot_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )
    
    # Error log file
    logger.add(
        LOGS_DIR / "errors_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="90 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR"
    )
    
    return logger


# Initialize logger
log = setup_logger()
