#!/usr/bin/python

from ytmusicapi import YTMusic
import os
import subprocess

yt = YTMusic()
alternate = 0

query = input("\033[1m\033[95mSearch: \033[0m")
search = yt.search(query, filter='albums')

for i in search:
    if alternate:
        color = '\033[94m'
        alternate = 0
    else:
        color = '\033[96m'
        alternate = 1
    print(color + '(' + str(search.index(i)+1) + ') ' + i['artists'][0]['name'] + ' - ' + i['title'] + '\033[0m')

print('\033[1m\033[93m(q) Exit\033[0m')
choice = input("\033[1m\033[95mChoose a number: \033[0m")

if choice.strip() == 'q':
    exit()

choices = choice.strip()

for choice in choices:
    albumId = search[int(choice)-1]['browseId']
    album = search[int(choice)-1]['title']
    artist = search[int(choice)-1]['artists'][0]['name']
    url = "https://music.youtube.com/playlist?list=" + yt.get_album(albumId)['audioPlaylistId']
    path = os.path.expanduser(f"~/Music/{artist}/{album}")

    subprocess.run(['mkdir', '-p', path])
    os.chdir(path)
    subprocess.run(['yt-dlp', '-f', 'm4a', '-o', '%(artist)s - %(track)s.%(ext)s', url])
