#!/usr/bin/python

from ytmusicapi import YTMusic as yt
import os
import subprocess


def main():
    query = input("\033[1m\033[95mSearch: \033[0m")
    search_results = yt.search(query, filter='albums')

    download_data = get_albums(search_results)
    download(download_data)


def get_albums(search_results):
    """
    :param search_results: List of albums found in youtube music database
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

        subprocess.run(['mkdir', '-p', path])
        os.chdir(path)
        subprocess.run(['yt-dlp', '-f', 'm4a', '-o', '%(first_artist)s - %(title)s.%(ext)s', '--parse-metadata',
                        'artist:^(?P<first_artist>[^,]+)', url])


if __name__ == '__main__':
    main()
