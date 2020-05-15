import textobjects.nodes as nodes
import re
from typing import List


wildcards = {'repeat':'!', 'optional':'?', 'search':'/'}
"""the supported wildcard modifiers for a placehoder"""

PLACEHOLDER_START, PLACEHOLDER_END = '{', '}'

PLACEHOLDER_PATTERN = re.compile(
        f'{PLACEHOLDER_START}(?P<name>\w+)' 
        '(<(?P<subexpr>.*(?=>))>)?'
        '(?P<wildcards>\D*)'
        f'(?P<limit>\d?\d?\d?){PLACEHOLDER_END}')
"""The pattern used to extract Placeholders from the template"""

DEFAULT_PLACEHOLDER_SUBEXPR = '\S+'
"""The pattern to be substituted when no pattern is specified for the placeholder eg. (**{name}**)"""

def apply_wildcards(placeholder, pattern, rt):
    """insert the appropriate nodes in the tree based on the given wildcards"""
    if isinstance(pattern, str):
        substitutions = re.findall('`.*?`', pattern)
    """substitutions are surrounded in backticks, this covers python & shell interpolation, 
    TextObject substitutions and previous match substitutions"""
    node = rt

    if placeholder:
        wcards = placeholder['wildcards']
        for wc in reversed(wcards): 
            if wc == wildcards['optional']:
                node = nodes.OptionalNode(name=placeholder['name'], parent=node)
            if wc == wildcards['repeat']:
                node = nodes.RepeatNode(name=placeholder['name'], parent=node)
            if wc == wildcards['search']:
                node = nodes.SearchNode(name=placeholder['name'], parent=node)

    name = placeholder['name'] if placeholder else None

    if isinstance(pattern, str):
        if substitutions:
            node = nodes.SubstitutionNode(name, pattern, substitutions=substitutions, parent=node)
        else:
            node = nodes.RegexMatchNode(name, pattern, parent=node)

    return node

def __parse(template):
    """break the template up into regex sections and placeholder sections"""
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

def parse(template, name=None, showtree=False, returntree=False):
    """create a StructuredText class from the given template
    
    Args: 
        template (str): the template string to parse
        name (str): The name for the class. If None is 
            given it will be called :class:`SomeTextObject`
        showtree (bool): If true a rendering of the execution tree
            will be printed
        returntree (bool): return the root node of the execution tree
            instead of a class

    Returns:
        (:obj:`StructuredText`) a StructuredText subclass based on the template string

    """
    parsedtemplate = __parse(template)
    rt = nodes.PatternNode(name)
    def _parse(rt, parsedtemplate):
        for ph, it in parsedtemplate:
            name = ph['name'] if ph else None
            if isinstance(it, List):
                _parse(apply_wildcards(ph, it, rt), it)
            else:
                apply_wildcards(ph, it, rt)
        return rt
    _parse(rt, parsedtemplate)
    if showtree:
        print(nodes.RenderTree(rt))
    if returntree:
        return rt
    return rt.textobjectclass

