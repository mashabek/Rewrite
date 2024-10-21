import logging
import io
import sys

# Create a StringIO object to capture logs
log_stream = io.StringIO()

# Configure the default logger
def setup_logger():
    logger = logging.getLogger('RewriterApp')
    logger.setLevel(logging.INFO)

    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    string_handler = logging.StreamHandler(log_stream)

    # Create formatter and add it to handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    string_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(string_handler)

    return logger

# Create and configure the logger
default_logger = setup_logger()