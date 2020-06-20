import parsy

from .utils import regex

"""
Rules for python identifiers:
https://docs.python.org/3.3/reference/lexical_analysis.html#identifiers

I don't know how to represent the NFKC normalization requirement in
regex, but I think it represents a subset of what the non-normalized
charsets capture, so our regex will be a bit too lenient, we can then
reject non-identifiers after the fact.
"""

ID_START = r"\p{Lu}\p{Ll}\p{Lt}\p{Lm}\p{Lo}\p{Nl}_\p{Other_ID_Start}"
ID_CONTINUE = ID_START + r"\p{Mn}\p{Mc}\p{Nd}\p{Pc}\p{Other_ID_Continue}"


@parsy.generate
def python_identifier() -> parsy.Parser:
    name = yield regex(f"[{ID_START}][{ID_CONTINUE}]*")
    if name.isidentifier():
        return name
    else:
        yield parsy.fail("Not a valid python identifier")
