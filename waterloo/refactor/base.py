from functools import wraps
from typing import List, Optional, Type

from bowler import LN, Capture, Filename, Query
from fissix.fixer_base import BaseFix

from waterloo.refactor.exceptions import Interrupt


class NonMatchingFixer(BaseFix):
    PATTERN = None  # type: ignore
    BM_compatible = False

    def match(self, node: LN) -> bool:
        # we don't need to participate in the matching phase, we just want
        # our `finish_tree` method to be called once after other modifiers
        # have completed their work...
        return False

    def transform(self, node: LN, capture: Capture) -> Optional[LN]:
        return node


class WaterlooQuery(Query):
    """
    Bowler's `Query.fixer()` method will take the Fixer you give it and replace
    it with their own class. This means there are some things you could do
    with a custom Fixer which won't be possible.

    So this class fixes that by allowing you to pass a custom Fixer that will
    be used as-is.

    See https://github.com/jreese/fissix/blob/master/fissix/fixer_base.py
    """

    raw_fixers: List[Type[BaseFix]]

    def __init__(self, *paths, **kwargs) -> None:
        super().__init__(*paths, **kwargs)
        self.raw_fixers = []

    def raw_fixer(self, fx: Type[BaseFix]) -> "WaterlooQuery":
        self.raw_fixers.append(fx)
        return self

    def compile(self) -> List[Type[BaseFix]]:
        fixers = super().compile()
        fixers.extend(self.raw_fixers)
        return fixers


def interrupt_modifier(f):
    @wraps(f)
    def decorated(node: LN, capture: Capture, filename: Filename) -> LN:
        try:
            return f(node=node, capture=capture, filename=filename)
        except Interrupt:
            return node

    return decorated
