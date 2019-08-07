from fissix import patcomp
from fissix.pgen2 import token


_original_type_of_literal = patcomp._type_of_literal


def _patched_type_of_literal(value):
    if value == '':
        return token.STRING
    return _original_type_of_literal(value)


patcomp._type_of_literal = _patched_type_of_literal
