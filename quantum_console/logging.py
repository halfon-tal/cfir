import logging

def init_logging(app):
    """Initialize logging for the Flask application."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Logging is set up.")
    return logger 