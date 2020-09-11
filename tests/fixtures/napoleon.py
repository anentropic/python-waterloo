"""
Boring docstring for the module itself
"""
import logging
from collections import namedtuple
from typing import NamedTuple, TypedDict, TypeVar, Union

import nott.so.serious
from ..sub import Irrelevant, Nonsense, Unused as ReallyUnused
from serious import *
from other.module import Product
from some.module import Imported
if True:
    from some.module import ConditionallyImported

logger = logging.getLogger(__name__)

SOME_CONST = 1


T = TypeVar('V')  # (deliberate name mismatch)

SomeTuple = namedtuple("_SomeTuple", ["val"])

SomeTypedTuple = NamedTuple("_SomeTypedTuple", (("val", str),))

SomeTypedDict = TypedDict("_SomeTypedDict", val=str)

NewClass = type("_NewClass", (object,), {})


class TopLevel(object):
    @staticmethod
    def static(cls, self):
        return cls, self

    @some_decorator(with_args)
    @classmethod
    def clsmethod(cls, self):
        """
        Args:
            self (Any)

        Returns:
            Any
        """
        return self

    def method(obj, cls):
        return cls

    if SOME_CONST:
        def conditionally_defined_method(obj, cls):
            return cls


def first(products, getter):
    """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
    tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
    veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
    commodo consequat.

    Args:
        products (Union[Iterable[Dict], Iterable[engine.models.Product]])
        getter (Callable[[str], Callable])

    Returns:
        Dict[int, List[ConditionallyImported]]: {<product id>: <product videos>}
    """
    from some.module import InnerImported
    print "Python 2 print statement"
    print("parenthesised print statement")
    return {}


def second(products, getter):
    """
    Duis aute irure dolor in reprehenderit in voluptate
    velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat
    cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id
    est laborum.

    Args:
        products (Iterable[engine.models.Product]): blah blah
        getter (Callable[[str], Callable]): something else

    Returns:
        Dict[int, List[TopLevel]]

    NOTE:
        whatever
    """
    class InnerClass(object):
        raise ValueError, "WTF python 2"

    def second_inner(product, key, default):
        """
        Args:
            product (Dict[str, Any])
            key (MysteryType[str]): this type has not been imported and is not
                defined in the document!
            default (Imported)

        Raises:
            ExceptionError
        """
        pass

    try:
        third([], 1)
    except ValueError, e:
        # disgusting Python 2.5 exception format
        pass
    return {}


def third(product_ids, user_id=None):
    """
    Donec massa sapien faucibus et molestie ac feugiat sed. Eget mi proin sed
    libero. Nulla aliquet enim tortor at auctor urna nunc. Massa placerat duis
    ultricies lacus sed turpis. Eleifend mi in nulla posuere sollicitudin
    aliquam ultrices.

    Kwargs:
        product_ids (List[int])
        user_id (Optional[int]): if given, also set the "liked" flag, meaning
            the current user has liked a product in the list
    """
    pass


def fourth(product_id, user_id):
    # type: (int, int) -> str
    """
    Already annotated
    """
    return 'whatever'


def fifth(product_ids, user_id=None):
    """
    Temporibus autem quibusdam et aut officiis debitis aut rerum necessitatibus
    saepe eveniet ut et voluptates repudiandae sint et molestiae non
    recusandae.

    Kwargs:
        product_ids: this arg has no type info
        user_id (Optional[int]): if given, also set the "liked" flag, meaning
            the current user has liked a product in the list

    Returns:
        bool
    """
    pass


def sixth(product_ids):
    """
    Temporibus autem quibusdam et aut officiis debitis aut rerum necessitatibus
    saepe eveniet ut et voluptates repudiandae sint et molestiae non
    recusandae.

    Args:
        product_ids (Iterable[int])

    Yields:
        int
    """
    for id_ in product_ids:
        yield id_
