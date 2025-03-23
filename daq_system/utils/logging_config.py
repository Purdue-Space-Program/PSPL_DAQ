"""
Logging configuration for the DAQ system.
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import os
import shutil
import sys


def setup_logging(log_dir: str = "logs") -> None:
    """
    Set up logging configuration with both file and console handlers.

    Args:
        log_dir: Directory to store log files
    """
    # Check if logging is already configured
    if logging.getLogger().handlers:
        return

    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Create a timestamp for the log file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"daq_system_{timestamp}.log"
    latest_log = log_path / "latest.log"

    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")

    # Set up file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10MB
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # Set up latest.log handler
    latest_handler = logging.FileHandler(latest_log, mode="w", encoding="utf-8")
    latest_handler.setLevel(logging.DEBUG)
    latest_handler.setFormatter(file_formatter)

    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove any existing handlers
    root_logger.handlers = []

    # Add our handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(latest_handler)
    root_logger.addHandler(console_handler)

    # Log a test message to verify logging is working
    root_logger.info("Logging system initialized successfully")
    root_logger.debug(f"Log files will be written to: {log_path.absolute()}")
    root_logger.debug(f"Latest log file: {latest_log.absolute()}")
