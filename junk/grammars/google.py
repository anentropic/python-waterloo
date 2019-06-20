import pyparsing as pp


SECTIONS = {
    'Args',
    'Arguments',
    'Attributes',
    'Example',
    'Examples',
    'Keyword Args',
    'Keyword Arguments',
    'Kwargs',  # not in Napoleon spec
    'Methods',
    'Note',
    'Notes',
    'Other Parameters',
    'Parameters',
    'Return',
    'Returns',
    'Raises',
    'References',
    'See Also',
    'Todo',
    'Warning',
    'Warnings',
    'Warns',
    'Yield',
    'Yields',
}

lpar = pp.Suppress('(')
rpar = pp.Suppress(')')
colon = pp.Suppress(':')

indent_stack = [1]

py_first = pp.Word(pp.alphas + "_", exact=1)
py_rest = pp.Word(pp.alphanums + "_")
py_identifier = pp.Combine(py_first + pp.Optional(py_rest))  # i.e. a variable name
qualified_py_identifier = pp.delimitedList(py_identifier, '.', combine=True)  # i.e. dotted path

py_type = pp.Forward()
py_type <<= qualified_py_identifier + pp.Optional('[' + pp.delimitedList(py_type) + ']')  # PEP-484 annotation

section_head = pp.oneOf(' '.join(SECTIONS))('section_name') + colon + pp.LineEnd().suppress()

type_value = pp.Group(py_type)
argument = py_identifier('name') + lpar + type_value('type') + rpar
term = type_value('type') ^ argument('argument')

token_start = section_head ^ (term + ':') ^ pp.StringEnd()
description = pp.Combine(
    pp.SkipTo(pp.LineEnd()) +
    pp.indentedBlock(
        pp.ZeroOrMore(
            pp.LineStart() + pp.SkipTo(pp.LineEnd())
        ),
        indent_stack
    )
)
definition = term + colon + description('description')

section = section_head + pp.indentedBlock(pp.OneOrMore(definition), indent_stack)('definitions')

docstring = pp.OneOrMore(section)
