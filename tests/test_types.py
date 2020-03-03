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
    assert example.to_annotation(None) == expected


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
    # TODO: name_to_strategy
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
     ArgTypes.factory(
        name=ArgsSection.ARGS,
        args=OrderedDict(),
     )),
    (set(),
     ArgTypes.factory(
        name=ArgsSection.ARGS,
        args=OrderedDict([
            ('a', None),
        ]),
     )),
    ({"str"},
     ArgTypes.factory(
        name=ArgsSection.ARGS,
        args=OrderedDict([
            ('a', TypeAtom("str", [])),
            ('b', TypeAtom("str", [])),
        ]),
     )),
    ({"Dict", "int", "str", "datetime"},
     ArgTypes.factory(
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
     ReturnType.factory(
        name=ReturnsSection.RETURNS,
        type_def=None,
     )),
    ({"str"},
     ReturnType.factory(
        name=ReturnsSection.RETURNS,
        type_def=TypeAtom("str", []),
     )),
    ({"Dict", "int", "str"},
     ReturnType.factory(
        name=ReturnsSection.RETURNS,
        type_def=TypeAtom("Dict", [
            TypeAtom("int", []), TypeAtom("str", [])
        ]),
     )),
])
def test_return_type_type_names(expected, example):
    assert example.type_names() == expected


@pytest.mark.parametrize('expected,example', [
    (set(),
     TypeSignature.factory(
        arg_types=None,
        return_type=None
     )),
    ({"str", "datetime"},
     TypeSignature.factory(
        arg_types=ArgTypes.factory(
            name=ArgsSection.ARGS,
            args=OrderedDict([
                ('a', TypeAtom("str", [])),
                ('b', TypeAtom("datetime", [])),
            ]),
        ),
        return_type=None
     )),
    ({"Dict", "int", "str"},
     TypeSignature.factory(
        arg_types=None,
        return_type=ReturnType.factory(
            name=ReturnsSection.RETURNS,
            type_def=TypeAtom("Dict", [
                TypeAtom("int", []), TypeAtom("str", [])
            ]),
        )
     )),
    ({"Dict", "int", "str", "datetime"},
     TypeSignature.factory(
        arg_types=ArgTypes.factory(
            name=ArgsSection.ARGS,
            args=OrderedDict([
                ('a', TypeAtom("str", [])),
                ('b', TypeAtom("datetime", [])),
            ]),
        ),
        return_type=ReturnType.factory(
            name=ReturnsSection.RETURNS,
            type_def=TypeAtom("Dict", [
                TypeAtom("int", []), TypeAtom("str", [])
            ]),
        )
     )),
])
def test_type_signature_type_names(expected, example):
    assert example.type_names() == expected
