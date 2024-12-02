import argparse
from dataclasses import dataclass
from typing import cast


@dataclass
class Args:
    """
    Data class representing command-line arguments.
    """

    is_song: bool
    is_debug: bool
    no_tag: bool
    dump_json: bool
    query: str
    dir: str

def parse_args() -> Args:
    """
    Parses command-line arguments.

    :returns: Parsed arguments as an instance of Args.
    """
    # Initialize parser
    parser = argparse.ArgumentParser(
        prog="muclic", description="A CLI for downloading music", exit_on_error=True
    )

    # Add arguments
    _ = parser.add_argument(
        "query", type=str, help="Album/song name", nargs="*", default=""
    )
    _ = parser.add_argument(
        "-d", "--dir", type=str, help="Specify output direcory", default="~/Music"
    )

    # Add switches
    _ = parser.add_argument(
        "-s",
        "--song",
        help="Download a single song",
        action="store_true",
        default=False,
    )
    _ = parser.add_argument(
        "-T", "--no-tag", help="Don't tag songs", action="store_true", default=False
    )
    _ = parser.add_argument(
        "--dump-json",
        help="Dump a single json file with info on downloaded items. For developement use only",
        action="store_true",
        default=False,
    )
    _ = parser.add_argument(
        "--debug", help="Set log level to debug", action="store_true", default=False
    )

    # Read arguments from command line and cast them to Args class
    args = parser.parse_args()

    args.query = " ".join(cast(str, args.query))

    return Args(
        is_song=cast(bool, args.song),
        is_debug=cast(bool, args.debug),
        no_tag=cast(bool, args.no_tag),
        dump_json=cast(bool, args.dump_json),
        query=args.query,
        dir=cast(str, args.dir),
    )
