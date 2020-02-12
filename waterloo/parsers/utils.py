from typing import Any, Generator, Tuple

import parsy

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
