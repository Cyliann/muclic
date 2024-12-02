import logging
from typing import override


# To comply with YoutubeDL logger
class YtDLLogger(logging.Logger):
    """
    Custom logger to integrate with YoutubeDL.
    """

    @override
    def debug(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        msg: str,
        *args: object,
        stack_info: bool = False,
        stacklevel: int = 1,
    ) -> None:
        """
        Overrides the debug method to reformat messages from YoutubeDL.

        :param msg: The message to log.
        :type msg: str
        :param *args: Additional arguments for logging.
        :type *args: object
        :param stack_info: Whether to include stack info.
        :type stack_info: bool
        :param stacklevel: The stack level for the log entry.
        :type stacklevel: int
        """
        if msg.startswith("[debug] "):
            super().debug(msg.removeprefix("[debug] "))
        else:
            self.info(msg)


def setup_logging(debug: bool) -> YtDLLogger:
    """
    Creates logger objects.

    :param debug: If loggers should use debug level
    :type debug: bool

    :return: An instance of YtDLLLogger to pass to YoutubeDL
    """
    logger = logging.getLogger(__name__)
    ytlogger = YtDLLogger("ytdl")

    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)
    ytlogger.setLevel(level)

    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    ytlogger.addHandler(handler)

    logger.debug("Logger set up")
    ytlogger.debug("[debug] YoutubeDL logger set up")

    return ytlogger
