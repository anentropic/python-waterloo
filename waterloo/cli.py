import argparse

from waterloo.annotator import annotate
from waterloo.conf import settings


def main():
    parser = argparse.ArgumentParser(
        description=(
            f"Convert the type annotations in 'Google-style' docstrings (as"
            f" understood by e.g. Sphinx's Napoleon docs plugin) "
            f" into PEP-484 type comments which can be checked statically"
            f" using `mypy --py2`"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        'files', metavar='F', type=str, nargs='+',  # required
        help='List of file or directory paths to process.',
    )

    indent_group = parser.add_argument_group('indentation options')
    indent_group.add_argument(
        '--indent', type=str, default="4",
        help="Due to multi-process architecture of the underlying Bowler "
        "refactoring tool we are unable to detect indents before processing "
        "each file. So specify your project's base indent as [tT] for tab or "
        "2|4|etc for no of spaces. (If you have multiple indent styles, do "
        "separate runs for each group of files, then think about your life "
        "choices...)"
    )
    indent_group.add_argument(
        '--max-indent-level', type=int, default=10,
        help="We have to generate pattern-matching indents in order to "
        "annotate functions, this is how many indent levels to generate "
        "matches for (indents larger than this will not be detected).",
    )

    annotation_group = parser.add_argument_group('annotation options')
    annotation_group.add_argument(
        '-aa', '--allow-untyped-args', action='store_true', default=False,
        help="If any args or return types are found in docstring we can "
        "attempt to output a type annotation. If arg types are missing or "
        "incomplete, default behaviour is to raise an error. If this flag "
        "is set we will instead output an annotation like `(...) -> returnT` "
        "which mypy will treat as if all args are `Any`."
    )

    apply_group = parser.add_argument_group('apply options')
    apply_group.add_argument(
        '-w', '--write', action='store_true', default=False,
        help="Whether to apply the changes to target files. Without this "
        "flag set waterloo will just perform a 'dry run'.",
    )
    apply_group.add_argument(
        '-s', '--show-diff', action='store_true', default=False,
        help="Whether to print the hunk diffs to be applied.",
    )
    apply_group.add_argument(
        '-i', '--interactive', action='store_true', default=False,
        help="Whether to prompt about applying each diff hunk.",
    )

    args = parser.parse_args()

    if args.indent.lower() == "t":
        indent = "\t"
    else:
        indent = " " * int(args.indent)

    settings.INDENT = indent
    settings.MAX_INDENT_LEVEL = args.max_indent_level
    settings.ALLOW_UNTYPED_ARGS = args.allow_untyped_args

    annotate(
        *args.files,
        interactive=args.interactive,
        write=args.write,
        silent=not args.show_diff,
    )
