import logging


def setup_logging(log_file: str = "calculator.log") -> logging.Logger:
    """Настраивает корневой логгер для записи сообщений DEBUG и выше в файл."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    file_formatter = logging.Formatter(
        '[%(asctime)s] - [%(name)s] - [%(levelname)s] - [%(message)s]'
    )

    file_handler = logging.FileHandler(log_file, encoding="UTF-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    logger.addHandler(file_handler)
    return logger