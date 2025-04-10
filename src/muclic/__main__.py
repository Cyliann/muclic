#!/usr/bin/python
# pyright: strict
# pyright: reportUnnecessaryTypeIgnoreComment=false
import logging
import os
import sys
import yt_dlp.version  # pyright: ignore[reportMissingTypeStubs]

import muclic.logging as logs
from muclic.app import App
from muclic.helper_types import SearchResult


def main() -> None:
    try:
        app = App()
        ytlogger: logs.YtDLLogger = logs.setup_logging(app.args.is_debug)

        if app.args.is_debug:
            logger = logging.getLogger()
            logger.debug(f"yt-dlp version: {yt_dlp.version.__version__}")

        search_results: list[SearchResult] = app.search()
        user_choices: list[int] = app.get_user_choices(search_results)

        app.create_media_items(user_choices, search_results)
        app.download_items(ytlogger)
        app.download_lyrics()
        temp_files = app.tag_items()

        # Cleanup
        for file in temp_files:
            os.remove(file)
    except KeyboardInterrupt:
        sys.exit(0)
    except ConnectionError as e:
        logger = logging.getLogger()
        logger.error("Check your connection: ", e)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
