import nodes
import re
from typing import List

wildcards = {'repeat':'!', 'optional':'?', 'search':'/'}

PLACEHOLDER_START, PLACEHOLDER_END = '{', '}'

PLACEHOLDER_PATTERN = re.compile(
        f'{PLACEHOLDER_START}(?P<name>\w+)' 
        '(<(?P<subexpr>.*(?=>))>)?'
        '(?P<wildcards>\D*)'
        f'(?P<limit>\d?\d?\d?){PLACEHOLDER_END}')
"""The pattern used to extract Placeholders from the template"""

DEFAULT_PLACEHOLDER_SUBEXPR = '\S+'
"""The pattern to be substituted when no pattern is specified for the placeholder eg. (**{name}**)"""

def node_by_wildcards(placeholder, pattern, rt):
    if not placeholder:
        return nodes.RegexMatchNode(None, pattern, rt)

    node = rt
    wcards = placeholder['wildcards']
    for wc in reversed(wcards):
        if wc == wildcards['optional']:
            node = nodes.OptionalNode(name=placeholder['name'], parent=node)
        if wc == wildcards['repeat']:
            node = nodes.RepeatNode(name=placeholder['name'], parent=node)
        if wc == wildcards['search']:
            node = nodes.SearchNode(name=placeholder['name'], parent=node)

    if isinstance(pattern, str):
        node = nodes.RegexMatchNode(placeholder['name'], pattern, node)
    return node

def __parse(template):
    rstack, pstack, results = [0], [], []
    for i, c in enumerate(template):
        if c == PLACEHOLDER_START:
            if not pstack:
                results.append((None, template[rstack.pop():i]))
            pstack.append(i)
        if c == PLACEHOLDER_END:
            start = pstack.pop()
            if not pstack:
                placeholder = template[start:i+1]
                parsed = PLACEHOLDER_PATTERN.match(placeholder).groupdict()
                if not parsed['subexpr']:
                    parsed['subexpr'] = DEFAULT_PLACEHOLDER_SUBEXPR
                if PLACEHOLDER_START in parsed['subexpr']:
                    results.append((parsed, __parse(parsed['subexpr'])))
                else:
                    results.append((parsed, parsed['subexpr']))
            rstack.append(i+1)
    results.append((None, template[rstack.pop():]))
    return [r for r in results if r[1]]

def parse(template, name=None):
    parsedtemplate = __parse(template)
    rt = nodes.PatternNode(name)
    def _parse(rt, parsedtemplate):
        for ph, it in parsedtemplate:
            name = ph['name'] if ph else None
            if isinstance(it, List):
                _parse(node_by_wildcards(ph, it, rt), it)
            else:
                node_by_wildcards(ph, it, rt)
        return rt
    _parse(rt, parsedtemplate)
    print(nodes.RenderTree(rt))
    return rt.textobjectclass



ToDo = parse('TODO: {item}', 'ToDo')

print(parse('\ToDo'))



