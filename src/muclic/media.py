from abc import ABC, abstractmethod
from dataclasses import dataclass

from muclic.helper_types import AlbumInfo, SongInfo
from muclic.logging import YtDLLogger


@dataclass
class MediaItem(ABC):
    """
    Abstract base class for media items.
    """

    title: str
    artist: str
    path: str
    url: str
    cover: str | None
    info: SongInfo | AlbumInfo | None

    @abstractmethod
    def download(self, ytlogger: YtDLLogger) -> None: ...

    @abstractmethod
    def download_lyrics(self) -> None: ...

    @abstractmethod
    def tag(self) -> None: ...

    def get_cover(self, temp_files: list[str]) -> None: ...  # pyright: ignore[reportUnusedParameter]
