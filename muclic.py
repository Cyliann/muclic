#!/usr/bin/python
from ytmusicapi import YTMusic
import os
from yt_dlp import YoutubeDL


class Record:
    def __init__(self, title, artist, path, url):
        self.title = title
        self.artist = artist
        self.path = path
        self.url = url


def main():
    query = input("\033[1m\033[95mSearch: \033[0m")
    yt = YTMusic()
    search_results = yt.search(query, filter="albums")
    download_data = get_albums(search_results, yt)
    download(download_data)


def get_albums(search_results, yt):
    """
    :param: search_results: List of albums found in YouTube Music database
    :return: List of data necessary to download album (urls, path, album name, artist name)
    """

    alternate = 0
    records = []

    for index, result in enumerate(search_results):
        if alternate:
            color = "\033[94m"
            alternate = 0
        else:
            color = "\033[96m"
            alternate = 1
        print(
            color
            + "("
            + str(index + 1)
            + ") "
            + result["artists"][1]["name"]
            + " - "
            + result["title"]
            + "\033[0m"
        )

    print("\033[1m\033[93m" + "(q) Exit" + "\033[0m")
    result = input("\033[1m\033[95m" + "Choose a number: " + "\033[0m")

    if result.strip().lower() == "q":
        exit()

    choices = result.split()

    for result in choices:
        album = search_results[int(result) - 1]

        album_id = album["browseId"]
        album_title = album["title"]
        artist = album["artists"][1]["name"]

        url = (
            "https://music.youtube.com/playlist?list="
            + yt.get_album(album_id)["audioPlaylistId"]
        )
        path = os.path.expanduser(f"~/Music/{artist}/{album_title}")

        record = Record(album_title, artist, path, url)

        records.append(record)

    return records


def download(download_data):
    """
    :param download_data: List of album data to download (url, path, album name, artist)
    :return: none
    """

    for record in download_data:
        url = record.url
        path = record.path
        artist = record.artist

        os.makedirs(path, mode=0o755, exist_ok=True)
        os.chdir(path)

        ydl_opts = {
            "format": "m4a/bestaudio",
            "forcejon": True,
            "dump_single_json": True,
            "outtmpl": {
                "default": f"{artist} - %(title)s.%(ext)s",
            },
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            tag_songs(info, path)


def tag_songs(info, path):
    """
    :param: info: json of all data yt_dlp dumps
    :param: path: path to the directory with songs to be tagged
    :return: none
    """

    try:
        import taglib
    except ModuleNotFoundError:
        print(
            "["
            + "\033[93m"
            + "Warning"
            + "\033[0m"
            + "] Module pytaglib not installed.\n"
            "["
            + "\033[93m"
            + "Warning"
            + "\033[0m"
            + "] Install it with 'pip install pytaglib'\n"
            "[" + "\033[93m" + "Warning" + "\033[0m" + "] Skipping tagging"
        )

        exit()

    for entry, file in zip(info["entries"], os.listdir(path)):
        song = taglib.File(file)
        song.tags["ARTIST"] = [entry["artist"].split(",")[0].encode("utf-8")]
        song.tags["ALBUM"] = [entry["album"].encode("utf-8")]
        song.tags["TITLE"] = [entry["track"].encode("utf-8")]

        if entry["release_year"] is not None:
            song.tags["DATE"] = [str(entry["release_year"]).encode("utf-8")]

        try:
            song.tags["GENRE"] = [
                entry["genre"].encode("utf-8")
            ]  # Some songs don't have 'genre' field
        except KeyError:
            pass

        try:  # Some songs don't have 'track_number' field
            song.tags["TRACKNUMBER"] = [entry["track_number"].encode("utf-8")]
        except KeyError:
            try:
                song.tags["TRACKNUMBER"] = [
                    str(entry["playlist_index"]).encode("utf-8")
                ]
            except KeyError:
                pass
        song.save()


if __name__ == "__main__":
    main()
