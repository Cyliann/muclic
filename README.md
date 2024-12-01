# MuCLIc - a cli for downloading music

This little Python script downloads music albums from YTMusic.

## Installation

```sh
pip install muclic
```

## Usage

1. Run `muclic`
2. Enter the name of the album|artist|song.
3. Choose a number/multiple numbers to select which album you want to download.
4. Press enter and enjoy the music.

## Arguments
```
positional arguments:
  query              Album/song name

options:
  -h, --help         show this help message and exit
  -d DIR, --dir DIR  Specify output direcory
  -s, --song         Download a single song
  -T, --no-tag       Don't tag songs
  --dump-json        Dump a single json file with info on downloaded items. For developement use only
  --debug            Set log level to debug
```

## For developement
### Install dependencies:

- [ytmusicapi](https://github.com/sigma67/ytmusicapi)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [mutagen](https://github.com/quodlibet/mutagen) (optional; for audio tagging)

```sh
pip install yt-dlp ytmusicapi mutagen
```
Run `src/muclic/muclic.py`
