import argparse

import inject

from waterloo.__about__ import __version__
from waterloo import configuration_factory
from waterloo.refactor import annotate
from waterloo.types import ImportCollisionPolicy, UnpathedTypePolicy


@inject.params(settings='settings')
def main(settings):
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

    annotation_group = annotate_cmd.add_argument_group('annotation options')
    annotation_group.add_argument(
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
        '-ic', '--import-collision-policy',
        default=settings.IMPORT_COLLISION_POLICY.name,
        choices=[m.name for m in ImportCollisionPolicy],
        help="There are some cases where it is ambiguous whether we need to "
        "add an import for your documented type. This can occur if you gave "
        "a dotted package path but there is already a matching `from package "
        "import *`, or a relative import of same type name. In both cases it "
        "is safest for us to add a new specific import for your type, but it "
        "may be redundant. The default option IMPORT will add imports. The "
        "NO_IMPORT option will annotate without adding imports, and will also "
        "show a warning message. FAIL will print an error and won't add any "
        "annotation."
    )
    annotation_group.add_argument(
        '-up', '--unpathed-type-policy',
        default=settings.UNPATHED_TYPE_POLICY.name,
        choices=[m.name for m in UnpathedTypePolicy],
        help="There are some cases where we cannot determine an appropriate "
        "import to add - when your types do not have a dotted path and we "
        "can't find a matching type in builtins, typing package or locals. "
        "When policy is IGNORE we will annotate as documented, you will need "
        "to resolve any errors raised by mypy manually. WARN option will "
        "annotate as documented but also display a warning. FAIL will print "
        "an error and won't add any annotation."
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
    elif args.subparser == "annotate":
        settings.PYTHON_VERSION = args.python_version
        settings.ALLOW_UNTYPED_ARGS = args.allow_untyped_args
        settings.REQUIRE_RETURN_TYPE = args.require_return_type
        settings.IMPORT_COLLISION_POLICY = args.import_collision_policy
        settings.UNPATHED_TYPE_POLICY = args.unpathed_type_policy

        inject.clear_and_configure(configuration_factory(settings))

        annotate(
            *args.files,
            interactive=args.interactive,
            write=args.write,
            silent=not args.show_diff,
        )
    else:
        parser.print_usage()