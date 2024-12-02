from abc import ABC, abstractmethod
from dataclasses import dataclass

from muclic.logging import YtDLLogger
from muclic.typing import AlbumInfo, SongInfo


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
    def tag(self) -> None: ...

    def get_cover(self, temp_files: list[str]) -> None: ...  # pyright: ignore[reportUnusedParameter]
