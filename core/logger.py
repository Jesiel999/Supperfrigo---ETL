import logging
import os
from concurrent_log_handler import ConcurrentRotatingFileHandler


def get_layer_logger(layer: str, name: str) -> logging.Logger:
    """
    Retorna um logger nomeado que grava em logs/<layer>/<name>.log
    além do handler raiz (console + errors).
    """
    log_dir = os.path.join("logs", layer)
    os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(log_dir, f"{name}.log")

    logger = logging.getLogger(f"{layer}.{name}")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if len(logger.handlers) == 0:
        fh = ConcurrentRotatingFileHandler(
            log_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=3
        )
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
