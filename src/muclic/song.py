# pyright: reportRedeclaration=none, reportMissingTypeStubs=none
import fnmatch
import logging
import os
import urllib.request
from dataclasses import dataclass
from typing import cast, override

from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic

from muclic.logging import YtDLLogger
from muclic.media import MediaItem
from muclic.typing import (
    AlbumInfo,
    AlbumSearchResult,
    SearchResult,
    SongInfo,
    SongSearchResult,
    Thumbnail,
)

THUMB_RES: int = 500


@dataclass
class Song(MediaItem):
    """
    Class representing a single song.
    """

    album_title: str
    song_id: str

    @override
    def download(self, ytlogger: YtDLLogger):
        """
        Downloads the song and retrieves its metadata.

        :param ytlogger: Instance of YtDLLogger for logging.
        :type ytlogger: YtDLLogger
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
                ydl.sanitize_info(ydl.extract_info(self.url)),  # pyright: ignore[reportUnknownMemberType]
            )

    @override
    def tag(self) -> None:
        """
        Tags the downloaded song file with metadata, including cover image.
        Expects self.info and self.cover to be valid.
        """
        from mutagen import mp4

        assert self.info is not None

        # asserting to SongInfo to silence the LSP
        # however TypedDicts are just dicts under the cover, so we cannot assert their type to be SongInfo, hence assert to dict
        # that's the stupidest useless line of code I have ever written
        assert (
            type(self.info) is SongInfo or type(self.info) is dict
        ), "that shouldn't be even possible"

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
    def get_cover(self, temp_files: list[str]) -> None:
        """
        Retrieves the album cover for the song based on its album title and artist.

        Gets the first thumbnail which width is greater or equal to THUMB_RES.
        Calls yt.search() to find an album with matching title and artists and fetches its cover.
        """
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
        # noqa: F821
        cover, _ = urllib.request.urlretrieve(cover_url)
        assert isinstance(cover, str)
        logger.debug(f"Path to the cover file is {os.path.abspath(cover)}")
        temp_files.append(cover)
        self.cover = cover


class SongFactory:
    """
    Factory class that handles creation of Song objects.
    """

    def createSongFromSearch(self, data: SearchResult, dir: str) -> Song:
        """
        Creates a Song object based on data from SearchResult.

        :param data: Data contained in a search result
        :type data: SearchResult
        :param dir: Path to the output directory
        :type dir: str
        """
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
        """
        Creates a Song object based on data from SongInfo.

        :param data: Data contained in album's 'entries' field
        :type data: SongInfo
        :param path: Path to the album directory ({output directory}/{album_name})
        :type path: str
        """
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
