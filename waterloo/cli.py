import argparse

from colored import style

from waterloo.annotator import annotate


def main():
    parser = argparse.ArgumentParser(
        description=(
            f"Convert the type annotations in 'Google-style' docstrings (as"
            f" understood by e.g. {style.DIM}sphinx.ext.napoleon{style.RESET})"
            f" into PEP-484 type comments which can be checked statically"
            f" using {style.DIM}mypy --py2{style.RESET}"
        )
    )
    parser.add_argument(
        'files', metavar='F', type=str, nargs='+',  # required
        help='file(s) to process',
    )

    parser.add_argument(
        '--indent', type=str, default="    ",
        help='we have to generate pattern-matching indents in order to '
        'annotate nested functions, this is how many indent levels to '
        'generate matches for (indents larger than this will not be '
        'detected)',
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
        '-s', '--show-diff', action='store_true', default=False,
        help='whether to print the hunk diffs to be applied',
    )

    args = parser.parse_args()

    annotate(
        *args.files,
        project_indent=args.indent,
        max_indent_level=args.max_indent_level,
        interactive=args.interactive,
        write=args.write,
        silent=not args.show_diff,
    )
