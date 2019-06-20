import re

import parsy as p


NL = p.string('\n')


# lexer:
blank_line = (
    (NL >> p.regex(r'^\s*$', flags=re.MULTILINE))
    .result((None, ''))
    .desc('blank line')
)
optional_indent = NL >> p.regex(r'^\s*', flags=re.MULTILINE).desc('optional indent')
rest_of_line = p.regex(r'.*$', flags=re.MULTILINE)
line = blank_line | p.seq(optional_indent, rest_of_line)


def indented_block(stack=None):
    if stack is None:
        stack = []

    @p.Parser
    def indent_parser(stream, index):
        start_index = index
        stream_len = len(stream)
        initial_indent = stack[-1] if stack else None
        new_indent = None
        indented_lines = []
        result = None
        while index < stream_len:
            result = line(stream, index).aggregate(result)
            if not result.status:
                if indented_lines:
                    # no more lines to find, return what we have
                    print('no more lines to find, return what we have')
                    break
                else:
                    # failed to find first line
                    print('failed to find first line')
                    return result

            indent_str, _ = result.value
            if indent_str is not None:
                # if not a blank line, check indent
                print('not a blank line, check indent')
                indent = len(indent_str)
                if initial_indent is not None and indent <= initial_indent:
                    # not indented any more
                    print('not indented any more initial:{} current:{}'.format(initial_indent, indent))
                    break
                if initial_indent is None:
                    initial_indent = indent
                if new_indent is None:
                    new_indent = indent
                    stack.append(indent)

            index = result.index
            indented_lines.append(result.value)

        print(indented_lines)
        stack.pop()
        return p.Result.success(index, stream[start_index: index]).aggregate(result)

    return indent_parser


# parser:
term = p.regex(r'[a-zA-Z0-9_]+')
description = rest_of_line + indented_block()
definition = optional_indent >> p.seq(term << p.string(':'), description)
