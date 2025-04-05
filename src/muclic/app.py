# pyright: reportRedeclaration=none, reportMissingTypeStubs=none
import logging
import sys
import json
from typing import cast

from requests.models import ReadTimeoutError
from ytmusicapi import YTMusic

import muclic.args as args
from muclic.album import AlbumFactory
from muclic.logging import YtDLLogger
from muclic.media import MediaItem
from muclic.song import SongFactory
from muclic.helper_types import SearchResult

RESET_COLOR: str = "\033[0m"
BOLD: str = "\033[1m"
COLOR1: str = "\033[94m"
COLOR2: str = "\033[96m"
COLOR3: str = "\033[93m"
COLOR4: str = "\033[95m"


class App:
    """
    Main application class for the CLI.
    """

    def __init__(self) -> None:
        self.args: args.Args = args.parse_args()
        self.yt: YTMusic | None = None
        self.items: list[MediaItem] = []

    def search(self) -> list[SearchResult]:
        """
        Searches for media based on provided query.

        Query is either in self.args.query or if not provided, user is asked directly.

        :returns: List of search results as a list of SearchResult
        """
        try:
            self.yt = YTMusic()
        except ReadTimeoutError:
            exit("That didn't work. Check your internet connection")

        if self.args.query.strip() == "":
            self.args.query = input(f"{BOLD}{COLOR4}Search: {RESET_COLOR}")

        filter = "songs" if self.args.is_song else "albums"

        results = self.yt.search(self.args.query, filter=filter)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

        if self.args.dump_json:
            with open("results.json", "w") as f:
                json.dump(results, f)

        return cast(list[SearchResult], results)

    def get_user_choices(self, search_results: list[SearchResult]) -> list[int]:
        """
        Handles printing search results, asking the user for input and parsing it to return a list of user's picks.

        :param: search_results: List of search results
        :type search_results: list[SearchResult]

        :return: choices: List of integers representing items chosen by the user
        """
        for index, result in enumerate(search_results):
            try:
                artist: str = result["artists"][1]["name"]
            except IndexError:
                artist: str = result["artists"][0]["name"]

            title: str = result["title"]
            if index % 2 == 0:
                color: str = COLOR1
            else:
                color: str = COLOR2
            print(f"{color}({str(index + 1)}) {artist} - {title}{RESET_COLOR}")

        print(f"{BOLD}{COLOR3}(q) Exit{RESET_COLOR}")

        while True:
            try:
                result = input(f"{BOLD}{COLOR4}Choose a number: {RESET_COLOR}")

                if result.strip().lower() == "q":
                    exit()

                choices = [int(choice) for choice in result.split()]
                break
            except ValueError:
                print("Invalid choice. Please input valid numbers.")

        return choices

    def create_media_items(
        self, user_choices: list[int], search_results: list[SearchResult]
    ) -> None:
        """
        Creates media objects based on search results and user picks.

        :param user_choices: list of user's picks from the search result list
        :type user_choices: list[int]
        :param search_results: list of search results returned by search()
        :type search_results: list[SearchResult]
        """
        assert self.yt is not None  # just to silence the LSP

        items: list[MediaItem] = []
        sf: SongFactory = SongFactory()
        af: AlbumFactory = AlbumFactory()

        if self.args.is_song:
            for choice in user_choices:
                item: MediaItem = sf.createSongFromSearch(
                    search_results[choice - 1], self.args.dir
                )
                items.append(item)
        else:
            for choice in user_choices:
                item: MediaItem = af.createAlbum(
                    search_results[choice - 1], self.args.dir
                )
                items.append(item)
        self.items = items

    def download_items(self, ytlogger: YtDLLogger) -> None:
        """
        Downloads all items contained in self.items.

        :param ytlogger: Logger to pass to YoutubeDL
        :type ytlogger: YtDLLLogger
        """
        for item in self.items:
            item.download(ytlogger)

        if self.args.dump_json:
            import json

            with open("info.json", "w") as f:
                json.dump([item.info for item in self.items], f)

    def download_lyrics(self) -> None:
        """
        Downloads lyrics for all items contained in self.items.
        """
        if not self.args.lyrics:
            return

        for item in self.items:
            item.download_lyrics()

    def tag_items(self) -> list[str]:
        """
        Tags all items contained in self.items.
        """
        temp_files: list[str] = []

        if self.args.no_tag:
            return temp_files

        if "mutagen" not in sys.modules:  # missing dependencies
            logger = logging.getLogger()
            logger.warning("Module mutagen not installed.")
            logger.warning("Install it with 'pip install mutagen' or run with -T flag.")
            logger.warning("Skipping tagging.")
            return temp_files

        for item in self.items:
            item.get_cover(temp_files)
            item.tag()

        return temp_files
