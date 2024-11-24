#!/usr/bin/python
# pyright: strict
# pyright: reportRedeclaration=none, reportMissingTypeStubs=none
# pyright: reportUnnecessaryTypeIgnoreComment=false
import argparse
import fnmatch
import logging
import os
import sys
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypedDict, cast, override

from requests.models import ReadTimeoutError
from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic

TAG = "mutagen" in sys.modules  # check if mutagen is installed
RESET_COLOR: str = "\033[0m"
BOLD: str = "\033[1m"
COLOR1: str = "\033[94m"
COLOR2: str = "\033[96m"
COLOR3: str = "\033[93m"
COLOR4: str = "\033[95m"
TEMP_FILES: list[str] = []
THUMB_RES: int = 500


class Thumbnail(TypedDict):
    width: int
    url: str


class SearchResult(TypedDict):
    title: str
    artists: list[dict[str, str]]


class SongSearchResult(SearchResult):
    videoId: str
    album: dict[str, str]


class AlbumSearchResult(SearchResult):
    browseId: str
    thumbnails: list[Thumbnail]


class YTAlbumData(TypedDict):
    audioPlaylistId: str


class SongInfo(TypedDict):
    release_year: int | None
    artist: str | list[str]
    album: str
    track: str
    genre: str
    track_number: int
    n_entries: int
    playlist_index: int
    thumbnails: list[Thumbnail]


class AlbumInfo(TypedDict):
    thumbnails: list[Thumbnail]
    entries: list[SongInfo]


# To comply with YoutubeDL logger
class YtDLLogger(logging.Logger):
    @override
    def debug(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        msg: str,
        *args: object,
        stack_info: bool = False,
        stacklevel: int = 1,
    ) -> None:
        if msg.startswith("[debug] "):
            super().debug(msg.removeprefix("[debug] "))
        else:
            self.info(msg)


@dataclass
class Args:
    is_song: bool
    is_debug: bool
    no_tag: bool
    dump_json: bool
    query: str
    dir: str


@dataclass
class MediaItem(ABC):
    title: str
    artist: str
    path: str
    url: str
    cover: str | None
    info: SongInfo | AlbumInfo | None

    @abstractmethod
    def download(self, ytlogger: YtDLLogger) -> None: ...

    @abstractmethod
    def tag(self) -> None: ...

    def get_cover(self) -> None: ...


@dataclass
class Song(MediaItem):
    album_title: str
    song_id: str

    @override
    def download(self, ytlogger: YtDLLogger):
        """
        :param item: Data necessary for download (url, path, album name, artist)
        :return: none
        """

        os.makedirs(self.path, mode=0o755, exist_ok=True)
        os.chdir(self.path)

        ydl_opts = {
            "format": "m4a/bestaudio",
            "outtmpl": {
                "default": f"{self.artist} - %(title)s.%(ext)s",
            },
            "logger": ytlogger,
        }

        with YoutubeDL(ydl_opts) as ydl:
            self.info: SongInfo | AlbumInfo | None = cast(
                SongInfo,
                ydl.sanitize_info(ydl.extract_info(self.url)),  # pyright: ignore[reportIgnoreCommentWithoutRule, reportUnknownMemberType]
            )

    @override
    def tag(self):
        from mutagen import mp4

        assert self.info is not None

        # asserting to SongInfo to silence the LSP.
        # However TypedDicts are just dicts under the cover, so we cannot assert their type to be SongInfo, hence assert to dict
        assert type(self.info) is SongInfo or type(self.info) is dict

        file = ""
        for potential_file in os.listdir(self.path):
            # Find the right file to tag
            if fnmatch.fnmatch(potential_file, f"*{self.info['track']}.*"):
                file = os.path.join(self.path, potential_file)

        logger = logging.getLogger(__name__)
        logger.info(f"Tagging file: {file}")
        tags = mp4.MP4(file).tags
        if tags is None:
            return

        assert self.cover is not None
        with open(self.cover, "rb") as cover_file:
            artist: str | list[str] = self.info["artist"]
            if isinstance(artist, str):
                tags["\xa9ART"] = artist.split(",")[0]
            else:
                tags["\xa9ART"] = artist[0]

            tags["\xa9alb"] = self.info["album"]
            tags["\xa9nam"] = self.info["track"]

            if self.info["release_year"] is not None:
                tags["\xa9day"] = str(self.info["release_year"])

            try:
                tags["\xa9gen"] = [
                    self.info["genre"]
                ]  # Some songs don't have 'genre' field
            except KeyError:
                pass

            try:  # Some songs don't have 'track_number' field
                tracks = self.info["track_number"]
                total = self.info["n_entries"]
                tags["trkn"] = [(tracks, total)]
            except KeyError:
                try:
                    tracks = self.info["playlist_index"]
                    total = self.info["n_entries"]
                    tags["trkn"] = [(tracks, total)]
                except KeyError:
                    pass

            tags["covr"] = [mp4.MP4Cover(cover_file.read())]
            tags.save(file)  # pyright: ignore[reportUnknownMemberType]

    @override
    def get_cover(self) -> None:
        logger = logging.getLogger(__name__)
        yt = YTMusic()
        logger.debug("Searching for matching album...")

        # search for an album that has a matching name and artist
        album_search_results: AlbumSearchResult = yt.search(  # pyright: ignore[reportAssignmentType, reportUnknownMemberType]
            query=f"{self.album_title} {self.artist}", filter="albums", limit=1
        )[0]

        assert "thumbnails" in album_search_results
        assert isinstance(album_search_results["thumbnails"], list)
        thumbnails: list[Thumbnail] = album_search_results["thumbnails"]

        logger.debug("Found matching album")
        cover_url = None
        for thumb in thumbnails:
            if "width" not in thumb:
                continue
            if thumb["width"] >= THUMB_RES:
                cover_url = thumb["url"]
                break

        if cover_url is None:
            cover_url = thumbnails[-1]["url"]

        cover, _ = urllib.request.urlretrieve(cover_url)
        logger.debug(f"Path to the cover file is {os.path.abspath(cover)}")
        TEMP_FILES.append(cover)
        self.cover = cover


@dataclass
class Album(MediaItem):
    album_id: str
    songs: list[Song]

    @override
    def download(self, ytlogger: YtDLLogger) -> None:
        """
        :param item: Data necessary for download (url, path, album name, artist)
        :return: none
        """

        os.makedirs(self.path, mode=0o755, exist_ok=True)
        os.chdir(self.path)

        ydl_opts = {
            "format": "m4a/bestaudio",
            "outtmpl": {
                "default": f"{self.artist} - %(title)s.%(ext)s",
            },
            "logger": ytlogger,
        }

        with YoutubeDL(ydl_opts) as ydl:
            self.info: AlbumInfo | SongInfo | None = cast(
                AlbumInfo,
                ydl.sanitize_info(ydl.extract_info(self.url)),  # pyright: ignore[reportIgnoreCommentWithoutRule, reportUnknownMemberType]
            )
        self.add_songs()

    @override
    def tag(self) -> None:
        for song in self.songs:
            song.cover = self.cover
            song.tag()

    @override
    def get_cover(self) -> None:
        assert self.info is not None
        logger = logging.getLogger(__name__)
        cover_url = None
        for thumb in self.info["thumbnails"]:
            if "width" not in thumb:
                continue
            if thumb["width"] >= THUMB_RES:
                cover_url = thumb["url"]
                break

        if cover_url is None:
            cover_url = self.info["thumbnails"][-1]["url"]

        cover, _ = urllib.request.urlretrieve(cover_url)
        logger.debug(f"path of cover is {os.path.abspath(cover)}")
        TEMP_FILES.append(cover)
        self.cover = cover

    def add_songs(self) -> None:
        assert self.info is not None
        assert "entries" in self.info

        mf = MediaFactory()
        entries: list[SongInfo] = self.info["entries"]
        for entry in entries:
            song: Song = mf.createSongFromSongInfo(entry, self.path)
            self.songs.append(song)


class App:
    def __init__(self) -> None:
        self.args: Args = self.parse_args()
        self.yt: YTMusic | None = None
        self.items: list[MediaItem] = []

    def parse_args(self) -> Args:
        # Initialize parser
        parser = argparse.ArgumentParser(
            prog="muclic", description="A CLI for downloading music", exit_on_error=True
        )

        # Add arguments
        _ = parser.add_argument(
            "query", type=str, help="Album/song name", nargs="*", default=""
        )
        _ = parser.add_argument(
            "-d", "--dir", type=str, help="Specify output direcory", default="~/Music"
        )

        # Add switches
        _ = parser.add_argument(
            "-s",
            "--song",
            help="Download a single song",
            action="store_true",
            default=False,
        )
        _ = parser.add_argument(
            "-T", "--no-tag", help="Don't tag songs", action="store_true", default=False
        )
        _ = parser.add_argument(
            "--dump-json",
            help="Dump a single json file with info on downloaded items. For developement use only",
            action="store_true",
            default=False,
        )
        _ = parser.add_argument(
            "--debug", help="Set log level to debug", action="store_true", default=False
        )

        # Read arguments from command line and cast them to Args class
        args = parser.parse_args()

        args.query = " ".join(cast(str, args.query))

        return Args(
            is_song=cast(bool, args.song),
            is_debug=cast(bool, args.debug),
            no_tag=cast(bool, args.no_tag),
            dump_json=cast(bool, args.dump_json),
            query=args.query,
            dir=cast(str, args.dir),
        )

    def search(self) -> list[SearchResult]:
        try:
            self.yt = YTMusic()
        except ReadTimeoutError:
            exit("That didn't work. Check your internet connection")

        if self.args.query.strip() == "":
            self.args.query = input(f"{BOLD}{COLOR4}Search: {RESET_COLOR}")

        filter = "songs" if self.args.is_song else "albums"
        return cast(list[SearchResult], self.yt.search(self.args.query, filter=filter))  # pyright: ignore[reportIgnoreCommentWithoutRule, reportUnknownMemberType]

    def get_user_choices(self, search_results: list[SearchResult]) -> list[int]:
        """
        :param: search_results: List of albums found in YouTube Music database
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
        assert self.yt is not None  # just to silence the LSP

        items: list[MediaItem] = []
        mf: MediaFactory = MediaFactory()

        if self.args.is_song:
            for choice in user_choices:
                item: MediaItem = mf.createSongFromSearch(
                    search_results[choice - 1], self.args.dir
                )
                items.append(item)
        else:
            for choice in user_choices:
                item: MediaItem = mf.createAlbum(
                    search_results[choice - 1], self.args.dir, self.yt
                )
                items.append(item)
        self.items = items

    def download_items(self, ytlogger: YtDLLogger) -> None:
        for item in self.items:
            item.download(ytlogger)

        if self.args.dump_json:
            import json

            with open("info.json", "w") as f:
                json.dump([item.info for item in self.items], f)

    def tag_items(self) -> None:
        for item in self.items:
            item.get_cover()
            item.tag()


class MediaFactory:
    def createSongFromSearch(self, data: SearchResult, dir: str) -> Song:
        data: SongSearchResult = cast(SongSearchResult, data)
        title: str = data["title"]

        try:
            artist: str = data["artists"][1]["name"]
        except IndexError:
            artist: str = data["artists"][0]["name"]

        album_title: str = data["album"]["name"]
        song_id: str = data["videoId"]

        url: str = f"https://music.youtube.com/watch?v={song_id}"
        path: str = os.path.expanduser(f"{dir}/{artist}/{album_title}")

        return Song(
            title,
            artist,
            path,
            url,
            cover=None,
            info=None,
            album_title=album_title,
            song_id=song_id,
        )

    def createSongFromSongInfo(self, data: SongInfo, path: str) -> Song:
        title: str = data["track"]
        artist: str = data["artist"][0]
        album_title: str = data["album"]
        path: str = f"{path}"

        return Song(
            title,
            artist,
            path,
            url="",
            cover=None,
            album_title=album_title,
            song_id="",
            info=data,
        )

    def createAlbum(self, data: SearchResult, dir: str, yt: YTMusic) -> Album:
        data: AlbumSearchResult = cast(AlbumSearchResult, data)
        title: str = data["title"]

        try:
            artist: str = data["artists"][1]["name"]
        except IndexError:
            artist: str = data["artists"][0]["name"]

        browse_id: str = data["browseId"]
        album_id: str = cast(YTAlbumData, cast(object, yt.get_album(browse_id)))[  # pyright: ignore[reportIgnoreCommentWithoutRule, reportUnknownMemberType]
            "audioPlaylistId"
        ]

        url: str = f"https://music.youtube.com/playlist?list={album_id}"
        path: str = os.path.expanduser(f"{dir}/{artist}/{title}")

        return Album(
            title,
            artist,
            path,
            url,
            info=None,
            cover=None,
            album_id=album_id,
            songs=[],
        )


def main() -> None:
    app = App()
    ytlogger: YtDLLogger = setup_logging(app.args.is_debug)
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

    app.tag_items()

    # Cleanup
    for file in TEMP_FILES:
        os.remove(file)


def setup_logging(debug: bool) -> YtDLLogger:
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


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
