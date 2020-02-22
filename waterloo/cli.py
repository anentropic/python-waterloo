import argparse

from waterloo.__about__ import __version__
from waterloo.refactor import annotate
from waterloo.conf import settings


def main():
    parser = argparse.ArgumentParser(
        description=(
            f"Convert the type annotations in 'Google-style' docstrings (as"
            f" understood by e.g. Sphinx's Napoleon docs plugin) "
            f" into PEP-484 type comments which can be checked statically"
            f" using `mypy --py2`"
        ),
    )

    subparsers = parser.add_subparsers(
        dest='subparser', title='commands',
    )

    version_cmd = subparsers.add_parser(
        "version",
        help="Echo current waterloo version.",
    )

    annotate_cmd = subparsers.add_parser(
        "annotate",
        help="Annotate a file or set of files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    annotate_cmd.add_argument(
        'files', metavar='F', type=str, nargs='+',  # required
        help='List of file or directory paths to process.',
    )

    indent_group = annotate_cmd.add_argument_group('indentation options')
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

    annotation_group = annotate_cmd.add_argument_group('annotation options')
    annotation_group.add_argument(
        '-aa', '--allow-untyped-args', action='store_true', default=False,
        help="If any args or return types are found in docstring we can "
        "attempt to output a type annotation. If arg types are missing or "
        "incomplete, default behaviour is to raise an error. If this flag "
        "is set we will instead output an annotation like `(...) -> returnT` "
        "which mypy will treat as if all args are `Any`."
    )
    annotation_group.add_argument(
        '-rr', '--require-return-type', action='store_true', default=False,
        help="If any args or return types are found in docstring we can "
        "attempt to output a type annotation. If the return type is missing "
        "our default behaviour is to assume function should be annotated as "
        "returning `-> None`. If this flag is set we will instead raise an "
        "error."
    )

    apply_group = annotate_cmd.add_argument_group('apply options')
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

    if args.subparser == "version":
        print(__version__)
        return

    if args.indent.lower() == "t":
        indent = "\t"
    else:
        indent = " " * int(args.indent)

    settings.INDENT = indent
    settings.MAX_INDENT_LEVEL = args.max_indent_level
    settings.ALLOW_UNTYPED_ARGS = args.allow_untyped_args
    settings.REQUIRE_RETURN_TYPE = args.require_return_type

    annotate(
        *args.files,
        interactive=args.interactive,
        write=args.write,
        silent=not args.show_diff,
    )
