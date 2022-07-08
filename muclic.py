#!/usr/bin/python

from ytmusicapi import YTMusic as yt
import os
import subprocess


def main():
    query = input("\033[1m\033[95mSearch: \033[0m")
    search = yt.search(query, filter='albums')

    download_data = get_albums(search)
    download(download_data)


def get_albums(search):
    alternate = 0
    paths = []
    urls = []
    album_list = []
    artist_list = []

    for i in search:
        if alternate:
            color = '\033[94m'
            alternate = 0
        else:
            color = '\033[96m'
            alternate = 1
        print(color + '(' + str(search.index(i) + 1) + ') ' + i['artists'][0]['name'] + ' - ' + i['title'] + '\033[0m')

    print('\033[1m\033[93m(q) Exit\033[0m')
    choice = input("\033[1m\033[95mChoose a number: \033[0m")

    if choice.strip().lower() == 'q':
        exit()

    choices = choice.split()

    for i, choice in enumerate(choices):
        album_id = search[int(choice) - 1]['browseId']
        album_title = search[int(choice) - 1]['title']
        artist = search[int(choice) - 1]['artists'][0]['name']
        urls.append("https://music.youtube.com/playlist?list=" + yt.get_album(album_id)['audioPlaylistId'])
        paths.append(os.path.expanduser(f"~/Music/{artist}/{album_title}"))
        album_list.append(album_title)
        artist_list.append(artist)

    return list(zip(urls, paths, album_list, artist_list))


def download(albums):
    for album in albums:
        url = album[0]
        path = album[1]

        subprocess.run(['mkdir', '-p', path])
        os.chdir(path)
        subprocess.run(['yt-dlp', '-f', 'm4a', '-o', '%(first_artist)s - %(title)s.%(ext)s', '--parse-metadata',
                        'artist:^(?P<first_artist>[^,]+)', url])


if __name__ == '__main__':
    main()
