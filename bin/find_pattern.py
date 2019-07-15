#!/usr/bin/env python
"""
adapted from:
http://svn.python.org/projects/sandbox/trunk/2to3/scripts/find_pattern.py

Script that makes determining PATTERN for a new fix much easier.

Figuring out exactly what PATTERN I want for a given fixer class is
getting tedious. This script will step through each possible subtree
for a given string, allowing you to select which one you want. It will
then try to figure out an appropriate pattern to match that tree. This
pattern will require some editing (it will be overly restrictive) but
should provide a solid base to work with and handle the tricky parts.

Usage:

    python find_pattern.py "g.throw(E, V, T)"

This will step through each subtree in the parse. To reject a
candidate subtree, hit enter; to accept a candidate, hit "y" and
enter. The pattern will be spit out to stdout.

For example, the above will yield a succession of possible snippets,
skipping all leaf-only trees. I accept

'g.throw(E, V, T)'

This causes find_pattern to spit out

power< 'g' trailer< '.' 'throw' >
           trailer< '(' arglist< 'E' ',' 'V' ',' 'T' > ')' > >


Some minor tweaks later, I'm left with

power< any trailer< '.' 'throw' >
       trailer< '(' args=arglist< exc=any ',' val=any [',' tb=any] > ')' > >

which is exactly what I was after.

Larger snippets can be placed in a file (as opposed to a command-line
arg) and processed with the -f option.
"""

__author__ = "Collin Winter <collinw@gmail.com>"

# Python imports
import json
import optparse
import os
import sys
from io import StringIO
from enum import IntEnum

from lib2to3 import pytree, patcomp
from lib2to3.pgen2 import driver, token
from lib2to3.pygram import python_symbols, python_grammar

# 3rd party
from termcolor import colored

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from waterloo.lib2to3tools.constants import Symbol, Token  # noqa: E402

driver = driver.Driver(python_grammar, convert=pytree.convert)


def main(args):
    parser = optparse.OptionParser(usage="find_pattern.py [options] [string]")
    parser.add_option("-f", "--file", action="store",
                      help="Read a code snippet from the specified file")

    # Parse command line arguments
    options, args = parser.parse_args(args)
    if options.file:
        tree = driver.parse_file(options.file)
    elif len(args) > 1:
        tree = driver.parse_stream(StringIO(args[1] + "\n"))
    else:
        print("You must specify an input file or an input string", file=sys.stderr)
        return 1

    examine_tree(tree)
    return 0


def examine_tree(tree):
    for node in tree.post_order():
        if isinstance(node, pytree.Leaf):
            continue
        elif node.parent is None:
            # the whole file
            continue
        elif node.parent.parent is not None:
            # a sub element of one of the top level structures
            continue

        print(repr(str(node)))

        print(colored(json.dumps(find_pattern(node)), 'green'))
        print('')


def find_pattern(node):
    """
    Angle-brackets in output indicate start and end of nested AST structures.
    According to pybowler examples the pattern language is not whitespace
    sensitive so you are free to reformat it across multiple lines for clarity
    e.g.

        funcdef<
            NAME
            NAME
            parameters<
                LPAR
                typedargslist<
                    NAME COMMA NAME EQUAL NAME
                >
                RPAR
            >
            COLON
            suite<
                NEWLINE
                INDENT
                simple_stmt<
                    STRING NEWLINE
                >
                simple_stmt<
                    return_stmt<
                        NAME
                        atom<
                            LBRACE RBRACE
                        >
                    >
                    NEWLINE
                >
                DEDENT
            >
        >
    """
    if isinstance(node, pytree.Leaf):
        # makes nice looking output, but pattern not recognised by the matcher:
        # token = TOKEN_MAP(node.type)
        # return token.name
        return repr(node.value)

    return (
        find_symbol(node.type) +
        "< " +
        " ".join(find_pattern(n) for n in node.children) +
        " >"
    )


def find_symbol(sym):
    for n, v in python_symbols.__dict__.items():
        if v == sym:
            return n


if __name__ == "__main__":
    sys.exit(main(sys.argv))
