import logging
import pathlib



def get_logger(log_name: str = None, stream_logging_level: str = logging.INFO, file_handler: bool = False,
               log_file_path: str = '', filename="base.log"):
    # ToDo: log_file_path not used. Remove here and at every usage.

    log_file_path = pathlib.Path.home() / ".birdwatchpy"
    log_file_path.mkdir(parents=True, exist_ok=True)

    # Overwrite log level. ToDO: Remove or handle log level using env
    stream_logging_level = logging.DEBUG

    if not log_name:
        log_name = 'base_logger'

    logger = logging.getLogger(log_name)

    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(stream_logging_level)

    formatter = logging.Formatter(
        '[%(levelname)s] | %(asctime)s | %(message)s | Function: %(module)s.%(funcName)s | lineNumber: %(lineno)s |')
    ch.setFormatter(formatter)
    logger.addHandler(ch)  # Now any messages recorded with logger.info() will be send to the console

    # Add file handler if requested by caller - could be set by an environment variable as well.
    if file_handler:
        #if not Path(log_file_path).parent.is_file():
        #    Path(log_file_path).mkdir(exist_ok=True)

        fh = logging.FileHandler(filename=(log_file_path / filename).as_posix())
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)  # Now any messages recorded with logger.info() or higher will be sent to the console via
        # the earlier-attached stream handler, as well as to a file by the newly attached FileHandler.

    return logger
