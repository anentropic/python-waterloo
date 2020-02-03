from collections import OrderedDict

import pytest

from waterloo.types import (
    ArgsSection,
    ArgTypes,
    ReturnsSection,
    ReturnType,
    TypeAtom,
    TypeSignature,
)


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
def test_type_atom_to_annotation(expected, example):
    assert example.to_annotation(False) == expected


@pytest.mark.parametrize('expected,example', [
    ("str", TypeAtom("str", [])),
    ("Dict", TypeAtom("Dict", [])),
    ("Dict[int, str]",
     TypeAtom("Dict", [
        TypeAtom("int", []),
        TypeAtom("str", [])
     ])),
    ("Dict[int, User]",
     TypeAtom("Dict", [
        TypeAtom("int", []),
        TypeAtom("db.models.User", [])
     ])),
    ("Container[int]",
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
def test_type_atom_to_annotation_fix_dotted_paths(expected, example):
    assert example.to_annotation(True) == expected


@pytest.mark.parametrize('expected,example', [
    ({"str"}, TypeAtom("str", [])),
    ({"Dict"}, TypeAtom("Dict", [])),
    ({"Dict", "int", "str"},
     TypeAtom("Dict", [
        TypeAtom("int", []),
        TypeAtom("str", [])
     ])),
    ({"Dict", "int", "db.models.User"},
     TypeAtom("Dict", [
        TypeAtom("int", []),
        TypeAtom("db.models.User", [])
     ])),
    ({"my.generic.Container", "int"},
     TypeAtom("my.generic.Container", [
        TypeAtom("int", [])
     ])),
    ({"Tuple", "int", "..."},
     TypeAtom("Tuple", [
        TypeAtom("int", []),
        TypeAtom("...", [])
     ])),
    ({"Callable", "int", "str", "Dict"},
     TypeAtom("Callable", [
        [TypeAtom("int", []),
         TypeAtom("str", [])],
        TypeAtom("Dict", [
            TypeAtom("int", []),
            TypeAtom("str", [])
        ])
     ])),
])
def test_type_atom_type_names(expected, example):
    assert example.type_names() == expected


@pytest.mark.parametrize('expected,example', [
    (set(),
     ArgTypes(
        name=ArgsSection.ARGS,
        args=OrderedDict(),
     )),
    (set(),
     ArgTypes(
        name=ArgsSection.ARGS,
        args=OrderedDict([
            ('a', None),
        ]),
     )),
    ({"str"},
     ArgTypes(
        name=ArgsSection.ARGS,
        args=OrderedDict([
            ('a', TypeAtom("str", [])),
            ('b', TypeAtom("str", [])),
        ]),
     )),
    ({"Dict", "int", "str", "datetime"},
     ArgTypes(
        name=ArgsSection.ARGS,
        args=OrderedDict([
            ('a', TypeAtom("Dict", [
                TypeAtom("int", []), TypeAtom("str", [])
            ])),
            ('b', TypeAtom("str", [])),
            ('c', TypeAtom("datetime", [])),
        ]),
     )),
])
def test_arg_types_type_names(expected, example):
    assert example.type_names() == expected


@pytest.mark.parametrize('expected,example', [
    (set(),
     ReturnType(
        name=ReturnsSection.RETURNS,
        type=None,
     )),
    ({"str"},
     ReturnType(
        name=ReturnsSection.RETURNS,
        type=TypeAtom("str", []),
     )),
    ({"Dict", "int", "str"},
     ReturnType(
        name=ReturnsSection.RETURNS,
        type=TypeAtom("Dict", [
            TypeAtom("int", []), TypeAtom("str", [])
        ]),
     )),
])
def test_return_type_type_names(expected, example):
    assert example.type_names() == expected


@pytest.mark.parametrize('expected,example', [
    (set(),
     TypeSignature(
        args=None,
        returns=None
     )),
    ({"str", "datetime"},
     TypeSignature(
        args=ArgTypes(
            name=ArgsSection.ARGS,
            args=OrderedDict([
                ('a', TypeAtom("str", [])),
                ('b', TypeAtom("datetime", [])),
            ]),
        ),
        returns=None
     )),
    ({"Dict", "int", "str"},
     TypeSignature(
        args=None,
        returns=ReturnType(
            name=ReturnsSection.RETURNS,
            type=TypeAtom("Dict", [
                TypeAtom("int", []), TypeAtom("str", [])
            ]),
        )
     )),
    ({"Dict", "int", "str", "datetime"},
     TypeSignature(
        args=ArgTypes(
            name=ArgsSection.ARGS,
            args=OrderedDict([
                ('a', TypeAtom("str", [])),
                ('b', TypeAtom("datetime", [])),
            ]),
        ),
        returns=ReturnType(
            name=ReturnsSection.RETURNS,
            type=TypeAtom("Dict", [
                TypeAtom("int", []), TypeAtom("str", [])
            ]),
        )
     )),
])
def test_type_signature_type_names(expected, example):
    assert example.type_names() == expected
