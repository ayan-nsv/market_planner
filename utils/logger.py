# import logging

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("company_app")


import logging

def setup_logger(name: str = "app", level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:  # Prevent adding duplicate handlers
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
