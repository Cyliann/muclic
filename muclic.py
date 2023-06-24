#!/usr/bin/python
from ytmusicapi import YTMusic
import os
from yt_dlp import YoutubeDL
import fnmatch
import sys


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
            info = ydl.sanitize_info(ydl.extract_info(url, download=True, process=True))

            tag_songs(info, path)


def tag_songs(info, path):
    """
    :param: info: json of all data yt_dlp dumps
    :param: path: path to the directory with songs to be tagged
    :return: none
    """

    try:
        from mutagen.mp4 import MP4
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

    for entry in info["entries"]:
        for file in os.listdir(path):
            # Find the right file to tag
            if fnmatch.fnmatch(file, f"*{entry['track']}.*"):
                print(f"[tagging] File: {file} Title: {entry['track']}")

                tags = MP4(file).tags

                if not tags:  # I put this here just to silence my IDE
                    continue

                tags["\xa9ART"] = entry["artist"].split(",")[0]
                tags["\xa9alb"] = entry["album"]
                tags["\xa9nam"] = entry["track"]

                if entry["release_year"] is not None:
                    tags["\xa9day"] = str(entry["release_year"])

                try:
                    tags["\xa9gen"] = [
                        entry["genre"]
                    ]  # Some songs don't have 'genre' field
                except KeyError:
                    pass

                try:  # Some songs don't have 'track_number' field
                    tracks = entry["track_number"]
                    total = entry["n_entries"]
                    tags["trkn"] = [(tracks, total)]
                except KeyError:
                    try:
                        tracks = entry["playlist_index"]
                        total = entry["n_entries"]
                        tags["trkn"] = [(tracks, total)]
                    except KeyError:
                        pass
                tags.save(file)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
