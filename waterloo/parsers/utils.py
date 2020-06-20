from typing import Any, Generator, Tuple

import parsy
import regex as better_re

from waterloo.types import SourcePos

TypedMarkReturnT = Tuple[SourcePos, Any, SourcePos]


def typed_mark(p: parsy.Parser, factory=lambda *args: args):
    @parsy.generate
    def marked() -> Generator[parsy.Parser, parsy.Parser, TypedMarkReturnT]:
        start = SourcePos(*(yield parsy.line_info))
        body = yield p
        end = SourcePos(*(yield parsy.line_info))
        return factory(start, body, end)

    return marked


def regex(exp, flags=0):
    """
    Parsy's `regex` combinator, updated to use `regex` library for
    better unicode support.
    """
    if isinstance(exp, str):
        exp = better_re.compile(exp, flags)

    @parsy.Parser
    def regex_parser(stream, index):
        match = exp.match(stream, index)
        if match:
            return parsy.Result.success(match.end(), match.group(0))
        else:
            return parsy.Result.failure(index, exp.pattern)

    return regex_parser
