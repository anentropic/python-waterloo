import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from waterloo.annotator import annotate


def main():
    parser = argparse.ArgumentParser(
        description='Convert Napoleon-style docstrings to mypy type annotations.'
    )
    parser.add_argument(
        'files', metavar='F', type=str, nargs='+',  # required
        help='file(s) to process',
    )

    parser.add_argument(
        '--max-indent-level', type=int, default=10,
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

    annotate(
        *args.files,
        max_indent_level=args.max_indent_level,
        interactive=args.interactive,
        write=args.write,
        silent=args.silent,
    )
