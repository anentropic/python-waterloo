import argparse
import os
import sys
from typing import Iterable

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from waterloo.reader import annotate_file


def process(
    files: Iterable[str],
    max_indent: int,
    interactive: bool,
    write: bool,
    silent: bool,
):
    # TODO: multiprocess
    for filename in files:
        annotate_file(
            filename,
            max_indent=max_indent,
            interactive=interactive,
            write=write,
            silent=silent,
        )


def main():
    parser = argparse.ArgumentParser(
        description='Convert Napoleon-style docstrings to mypy type annotations.'
    )
    parser.add_argument(
        'files', metavar='F', type=str, nargs='+',  # required
        help='file(s) to process',
    )

    parser.add_argument(
        '--max-indent-level', type=int, default=8,
        help='we have to generate pattern-matching indents in order to '
        'annotate nested functions, this is how many indent levels to '
        'generate matches for (indents larger than this will not be '
        'detected)',
    )

    parser.add_argument(
        '-i', '--interactive', action='store_true', default=False,
        help='whether to prompt about applying each diff hunk',
    )
    parser.add_argument(
        '-w', '--write', action='store_true', default=False,
        help='whether to apply the changes to target files',
    )
    parser.add_argument(
        '-s', '--silent', action='store_true', default=False,
        help='whether to print the hunk diffs to be applied',
    )

    args = parser.parse_args()

    process(
        files=args.files,
        max_indent=args.max_indent_level,
        interactive=args.interactive,
        write=args.write,
        silent=args.silent,
    )
