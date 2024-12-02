from typing import TypedDict


class Thumbnail(TypedDict):
    """
    Represents a thumbnail image with its width and URL pointing to it.
    """

    width: int
    url: str


class SearchResult(TypedDict):
    """
    Result of a youtubemusic search independently of the filter.
    Has more fields, but we care only about those.
    """

    title: str
    artists: list[dict[str, str]]


class SongSearchResult(SearchResult):
    """
    Result of a youtubemusic search with a 'songs' filter.
    Has more fields, but we care only about those.
    """

    videoId: str
    album: dict[str, str]


class AlbumSearchResult(SearchResult):
    """
    Result of a youtubemusic search with a 'albums' filter.
    Has more fields, but we care only about those.
    """

    browseId: str
    thumbnails: list[Thumbnail]


class YTAlbumData(TypedDict):
    """
    Data received from downloading album from YTMusic.
    Has more fields, but we care only about those.
    """

    audioPlaylistId: str


class SongInfo(TypedDict):
    """
    Info dumped by YoutubeDL.
    Has more fields, but only these are needed for tagging.
    """

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
    """
    Info dumped by YoutubeDL.
    Has more fields, but only these are needed for tagging.
    """

    thumbnails: list[Thumbnail]
    entries: list[SongInfo]
