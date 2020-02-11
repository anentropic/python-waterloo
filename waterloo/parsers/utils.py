from typing import Any, Tuple

import parsy

from waterloo.types import SourcePos


def typed_mark(p: parsy.Parser, factory=lambda *args: args):
    @parsy.generate
    def marked() -> Tuple[SourcePos, Any, SourcePos]:
        start = SourcePos(*(yield parsy.line_info))
        body = yield p
        end = SourcePos(*(yield parsy.line_info))
        return factory(start, body, end)

    return marked
