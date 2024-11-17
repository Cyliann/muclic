# MuCLIc - a cli for downloading music

This little Python script downloads music albums from YTMusic.

## Installation

### Linux

```sh
curl -sL https://github.com/Cyliann/muclic/raw/main/muclic.py &&
chmod +x muclic.py
```

### Windows

Download the [muclic.py](./muclic.py) and put it in your home directory.

## Dependencies

- Python
- [ytmusicapi](https://github.com/sigma67/ytmusicapi)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)

### Optional

- [mutagen](https://github.com/quodlibet/mutagen) (for audio tagging)

Install through pip:

```sh
pip install yt-dlp ytmusicapi mutagen
```

## Usage

1. Type `muclic.py` into your terminal. (or `python -m muclic.py` if you're a Windows user)
2. Enter the name of the album|artist|song.
3. Choose a number/multiple numbers to select which album you want to download.
4. Press enter and enjoy the music.
