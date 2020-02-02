import pytest

from waterloo.types import TypeAtom


@pytest.mark.parametrize('expected,example', [
    ("str", TypeAtom("str", [])),
    ("Dict", TypeAtom("Dict", [])),
    ("Dict[int, str]",
     TypeAtom("Dict", [
        TypeAtom("int", []),
        TypeAtom("str", [])
     ])),
    ("Dict[int, db.models.User]",
     TypeAtom("Dict", [
        TypeAtom("int", []),
        TypeAtom("db.models.User", [])
     ])),
    ("my.generic.Container[int]",
     TypeAtom("my.generic.Container", [
        TypeAtom("int", [])
     ])),
    ("Tuple[int, ...]",
     TypeAtom("Tuple", [
        TypeAtom("int", []),
        TypeAtom("...", [])
     ])),
    ("Callable[[int, str], Dict[int, str]]",
     TypeAtom("Callable", [
        [TypeAtom("int", []),
         TypeAtom("str", [])],
        TypeAtom("Dict", [
            TypeAtom("int", []),
            TypeAtom("str", [])
        ])
     ])),
])
def test_type_atom_to_str(expected, example):
    assert example.to_annotation() == expected
