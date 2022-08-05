#!/usr/bin/python
from ytmusicapi import YTMusic
import os
from yt_dlp import YoutubeDL


def main():
    query = input("\033[1m\033[95mSearch: \033[0m")
    yt = YTMusic()
    search_results = yt.search(query, filter='albums')
    download_data = get_albums(search_results, yt)
    download(download_data)


def get_albums(search_results, yt):
    """
    :param: search_results: List of albums found in YouTube Music database
    :return: List of data necessary to download album (urls, path, album name, artist name)
    """

    alternate = 0
    paths = []
    urls = []
    album_list = []
    artist_list = []

    for index, i in enumerate(search_results):
        if alternate:
            color = '\033[94m'
            alternate = 0
        else:
            color = '\033[96m'
            alternate = 1
        print(color + '(' + str(index + 1) + ') ' + i['artists'][0]['name'] + ' - ' + i['title'] + '\033[0m')

    print('\033[1m\033[93m(q) Exit\033[0m')
    i = input("\033[1m\033[95mChoose a number: \033[0m")

    if i.strip().lower() == 'q':
        exit()

    choices = i.split()

    for i in choices:
        album = search_results[int(i) - 1]

        album_id = album['browseId']
        album_title = album['title']
        artist = album['artists'][0]['name']

        urls.append("https://music.youtube.com/playlist?list=" + yt.get_album(album_id)['audioPlaylistId'])
        paths.append(os.path.expanduser(f"~/Music/{artist}/{album_title}"))
        album_list.append(album_title)
        artist_list.append(artist)

    return list(zip(urls, paths, album_list, artist_list))


def download(download_data):
    """
    :param download_data: List of album data to download (url, path, album name, artist)
    :return: none
    """

    for album in download_data:
        url = album[0]
        path = album[1]
        artist = album[3]

        os.makedirs(path, mode=0o755, exist_ok=True)
        os.chdir(path)

        ydl_opts = {
            'format': 'm4a/bestaudio',
            'forcejon': True,
            'dump_single_json': True,
            'outtmpl': {
                'default': f'{artist} - %(title)s.%(ext)s',
            }
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
    import taglib

    for entry, file in zip(info['entries'], os.listdir(path)):
        song = taglib.File(file)
        song.tags['ARTIST'] = [entry['artist'].split(',')[0].encode('utf-8')]
        song.tags['ALBUM'] = [entry['album'].encode('utf-8')]
        song.tags['TITLE'] = [entry['track'].encode('utf-8')]

        if entry['release_year'] is not None:
            song.tags['DATE'] = [entry['release_year'].encode('utf-8')]

        try:
            song.tags['GENRE'] = [entry['genre'].encode('utf-8')]  # Some songs don't have 'genre' field
        except KeyError:
            pass

        try:
            song.tags['TRACKNUMBER'] = [
                entry['track_number'].encode('utf-8')]  # Some songs don't have 'track_number' field
        except KeyError:
            try:
                song.tags['TRACKNUMBER'] = [str(entry['playlist_index']).encode('utf-8')]
            except KeyError:
                pass
        song.save()


if __name__ == '__main__':
    main()
