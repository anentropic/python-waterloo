"""
Boring docstring for the module itself
"""
import logging

logger = logging.getLogger(__name__)

SOME_CONST = 1


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
        Dict[int, List[Dict]]: {<product id>: <product videos>}
    """
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
        Dict[int, List[Dict]]

    NOTE:
        whatever
    """
    def second_inner(product, key, default):
        """
        Args:
            product (Dict[str, Any])
            key (MysteryType[str])
            default (Any)

        Raises:
            ExceptionError
        """
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
