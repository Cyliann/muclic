# MuCLIc - a cli for downloading music

This little Python script downloads music albums from YTMusic.

## Installation

### Linux

```sh
sudo curl -sL https://github.com/Cyliann/muclic/raw/main/muclic.py -o /usr/bin/muclic &&
sudo chmod +x /usr/bin/muclic
```

### Windows

Download the [muclic.py](./muclic.py) and put it in your home directory.

## Dependencies

- Python
- [YTMusicAPI](https://github.com/sigma67/ytmusicapi)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (youtube-dl won't work because it doesn't support output formatting)

### Optional

- [pytaglib](https://github.com/supermihi/pytaglib) (for basic tagging)

To dowload dependencies just paste this into your terminal (if you have pip installed)

```sh
pip install yt-dlp ytmusicapi pytaglib
```

## Usage

1.  Type `muclic` into your terminal. (or `python -m muclic.py` if you're a Windows user)
2.  Enter the name of the album/artist/song.
3.  Choose a number/multiple numbers to select which album you want to download.
4.  Rest.

## To do

- Single song support
