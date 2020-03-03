import argparse

from waterloo.__about__ import __version__
from waterloo.conf import settings
from waterloo.refactor import annotate
from waterloo.types import AmbiguousTypePolicy


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

    subparsers.add_parser(
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

    general_group = annotate_cmd.add_argument_group('general options')
    general_group.add_argument(
        '-p', '--python-version', type=str,
        default=settings.PYTHON_VERSION,
        help="We can refactor either Python 2 or Python 3 source files but "
        "the underlying bowler+fissix libraries need to know which grammar "
        "to use (to know if `print` is a statement or a function). In Py2 "
        "mode, `print` will be auto-detected based on whether a `from "
        "__future__ import print_function` is found. For Py3 files `print` "
        "can only be a function. We also use `parso` library which can "
        "benefit from knowing <major>.<minor> version of your sources."
    )

    annotation_group = annotate_cmd.add_argument_group('annotation options')
    annotation_group.add_argument(
        '-aa', '--allow-untyped-args', action='store_true',
        default=settings.ALLOW_UNTYPED_ARGS,
        help="If any args or return types are found in the docstring we can "
        "attempt to output a type annotation. If arg types are missing or "
        "incomplete, default behaviour is to raise an error. If this flag "
        "is set we will instead output an annotation like `(...) -> returnT` "
        "which mypy will treat as if all args are `Any`."
    )
    annotation_group.add_argument(
        '-rr', '--require-return-type', action='store_true',
        default=settings.REQUIRE_RETURN_TYPE,
        help="If any args or return types are found in the docstring we can "
        "attempt to output a type annotation. If the return type is missing "
        "our default behaviour is to assume function should be annotated as "
        "returning `-> None`. If this flag is set we will instead raise an "
        "error."
    )
    annotation_group.add_argument(
        '-tp', '--ambiguous-type-policy',
        default=settings.AMBIGUOUS_TYPE_POLICY.name,
        choices=[m.name for m in AmbiguousTypePolicy],
        help="There are some cases where we either cannot determine an "
        "appropriate import to add, or it is ambiguous whether one is needed. "
        "If you have given a dotted-path to the type in your docstring then "
        "when policy is AUTO we will annotate and add import with no warning. "
        "(In cases where there is a matching `from package import *`, or a "
        "relative import of same type name, then this can lead to redundant "
        "imports). WARN option will annotate without adding imports in these "
        "cases, while FAIL will print an error and won't add any annotation. "
        "If you haven't given a dotted path to types then AUTO will behave as "
        "FAIL, while WARN will add an annotation without adding an import, as "
        "per above."
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

    settings.PYTHON_VERSION = args.python_version
    settings.ALLOW_UNTYPED_ARGS = args.allow_untyped_args
    settings.REQUIRE_RETURN_TYPE = args.require_return_type
    settings.AMBIGUOUS_TYPE_POLICY = args.ambiguous_type_policy

    annotate(
        *args.files,
        interactive=args.interactive,
        write=args.write,
        silent=not args.show_diff,
    )
