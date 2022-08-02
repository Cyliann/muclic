# MuCLIc - a cli for downloading music
This little Python script downloads music albums from YTMusic.


# Installation

Just download the script and put it in your executables directory (eg. `/usr/bin/` or `~/.local/bin/`) or your home direcotry if you're a Windows user.

## Dependencies

 - Python
 - [YTMusicAPI](https://github.com/sigma67/ytmusicapi)
 - [yt-dlp](https://github.com/yt-dlp/yt-dlp) (youtube-dl won't work because it doesn't support output formatting)
 
 To dowload dependencies just paste this into your terminal

    pip install yt-dlp ytmusicapi

## Usage

 1. Type `muclic.py` into your terminal. (or `python -m muclic.py` if you're a Windows user)
 2. Enter the name of the album/artist/song.
 3. Choose a number/multiple numbers to choose which album you want to download.
 4. Rest.

## To do

 - Auto ID3 tagging
 - In-line command options
