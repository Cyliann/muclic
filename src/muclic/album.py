# pyright: reportRedeclaration=none, reportMissingTypeStubs=none
import logging
import os
import urllib.request
from dataclasses import dataclass
from typing import cast, override

from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic

from muclic.logging import YtDLLogger
from muclic.media import MediaItem
from muclic.song import Song, SongFactory
from muclic.typing import (
    AlbumInfo,
    AlbumSearchResult,
    SearchResult,
    SongInfo,
    YTAlbumData,
)

THUMB_RES: int = 500


@dataclass
class Album(MediaItem):
    """
    Class representing an album.
    """

    album_id: str
    songs: list[Song]

    @override
    def download(self, ytlogger: YtDLLogger) -> None:
        """
        Downloads the album and retrieves its metadata.

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
            self.info: AlbumInfo | SongInfo | None = cast(
                AlbumInfo,
                ydl.sanitize_info(ydl.extract_info(self.url)),  # pyright: ignore[reportUnknownMemberType]
            )
        self.add_songs()

    @override
    def tag(self) -> None:
        """
        Tags the downloaded album file with metadata, including cover image.
        Expects self.info and self.cover to be valid.
        """
        for song in self.songs:
            song.cover = self.cover
            song.tag()

    @override
    def get_cover(self, temp_files: list[str]) -> None:
        """
        Retrieves the album cover.

        Gets the first thumbnail which width is greater or equal to THUMB_RES.
        """
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
        temp_files.append(cover)
        self.cover = cover

    def add_songs(self) -> None:
        """
        Populates self.songs with songs based on self.info
        """
        assert self.info is not None
        assert "entries" in self.info

        mf = SongFactory()
        entries: list[SongInfo] = self.info["entries"]
        for entry in entries:
            song: Song = mf.createSongFromSongInfo(entry, self.path)
            self.songs.append(song)


class AlbumFactory:
    """
    Factory class that handles creation of Album objects.
    """

    def createAlbum(self, data: SearchResult, dir: str, yt: YTMusic) -> Album:  # noqa: F821
        """
        Creates an Album object based on data from a search result.

        :param data: Data contained in a search result
        :type data: SearchResult
        :param dir: Path to the output directory
        :type dir: str
        :param yt: Instance of YTMusic, needed to find album's id
        :type yt: YTMusic
        """
        data: AlbumSearchResult = cast(AlbumSearchResult, data)
        title: str = data["title"]

        try:
            artist: str = data["artists"][1]["name"]
        except IndexError:
            artist: str = data["artists"][0]["name"]

        browse_id: str = data["browseId"]
        album_id: str = cast(YTAlbumData, cast(object, yt.get_album(browse_id)))[  # pyright: ignore[reportUnknownMemberType]
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
