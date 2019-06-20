import pyparsing as pp


NL = pp.LineEnd().suppress()

label = pp.ungroup(pp.Word(pp.alphas, pp.alphanums+'_') + pp.Suppress(":"))

indent_stack = [1]
description = pp.Group(
    pp.restOfLine + NL +
    pp.Optional(
        pp.ungroup(
            ~pp.StringEnd() +
            pp.indentedBlock(
                pp.restOfLine,
                indent_stack
            )
        )
    )
)

labeled_text = pp.Group(label("term") + description("description"))


def combine_parts(tokens):
    # recombine description parts into a single list
    tt = tokens[0]
    new_desc = [tt.description[0]]
    new_desc.extend(t[0] for t in tt.description[1:])

    # reassign rebuild description into the parsed token structure
    tt['description'] = new_desc
    tt[1][:] = new_desc


labeled_text.addParseAction(combine_parts)

grammar = pp.OneOrMore(labeled_text)
