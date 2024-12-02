#!/usr/bin/python
# pyright: strict
# pyright: reportUnnecessaryTypeIgnoreComment=false
import logging
import os
import sys

import muclic.logging as logs
from muclic.app import App
from muclic.typing import SearchResult

TAG = "mutagen" in sys.modules  # check if mutagen is installed


def main() -> None:
    app = App()
    ytlogger: logs.YtDLLogger = logs.setup_logging(app.args.is_debug)
    search_results: list[SearchResult] = app.search()
    user_choices: list[int] = app.get_user_choices(search_results)

    app.create_media_items(user_choices, search_results)
    app.download_items(ytlogger)

    if app.args.no_tag:
        return

    if not TAG:  # missing dependencies
        logger = logging.getLogger(__name__)
        logger.warning("Module pytaglib not installed.")
        logger.warning("Install it with 'pip install pytaglib'")
        logger.warning("Skipping tagging")
        return

    temp_files = app.tag_items()

    # Cleanup
    for file in temp_files:
        os.remove(file)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
