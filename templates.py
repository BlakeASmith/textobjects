"""Convert between template strings and regular expressions

Supported Syntax:
    {var}        |  to mark a placeholder with the name `var`
    {var<regex>} |  to mark a placeholder which matches the regex `regex`
    !            |  to repeat a placeholder any number of times
    !!           |  same as `!` but will allow non-matching text in between matches
    ?            |  to mark a placeholder as being optional
    @Name        |  embed another text object with class name `Name`
"""
import re
from anytree import NodeMixin, RenderTree
from functools import reduce
from itertools import takewhile

class TextNode(NodeMixin):
    """A Node which contains a substring of a larger body of text"""
    def __init__(self, text=None, parent=None, children=None):
        self.text = text
        self.expanded_text = None
        self.wildcards = None
        self.parent = parent
        if children:
            self.children = children

    def __init_subclass__(cls, outer_text, *args, **kwargs):
        super(TextNode, cls).__init_subclass__(*args, **kwargs)
        cls.outer_text = outer_text

    def __str__(self):
        return self.expanded_text or self.text

    def __repr__(self):
        return self.expanded_text or self.text

def build_tree(template):
    """create a tree associating outer placeholders to inner placeholders"""
    class Placeholder(TextNode, outer_text=template): pass

    stack = [] 
    root = cur_node = Placeholder(template)
    level = 0 # track the level of nesting
    for i, c in enumerate(template):
        if c == '{':
            cur_node = Placeholder(parent=cur_node)
            level += 1
            stack.append(i)
        elif c == '}':
            level -= 1
            cur_node.text = template[stack.pop():i+1]
            cur_node = cur_node.parent

    return root

def expanded(s, node):
    # convert simple placeholders to regex placeholders
    exp = re.sub('{(\w+?)}', '{\g<1><.+(?=\\\\s)>}', s)
    # extract name, regex, and wildcards
    placeholder = re.compile('{(?P<var>\w*)<(?P<subexpr>.*?)>(?P<wildcards>!?!?\??(?P<num>\d?\d?\d?))}')
    placeholders = [m.groupdict() for m in placeholder.finditer(s)]

    exp = placeholder.sub('(?P<\g<var>>\g<subexpr>)', exp)
    return exp

def expand(template):
    root = build_tree(template)
    def _expand(root):
        if not root.children:
            return expanded(root.text, node=root)
        for child in root.children:
            root.text = expanded(root.text.replace(child.text, _expand(child)), node=root)
        return root.text
    return _expand(root)

def indexed(template):
    elements = []
    regexstack, bracestack = [], []
    regexstack.append(0)
    placeholder = re.compile('{(?P<name>\w+\d*)<?(?P<subexpr>.*(?=>))?>?(?P<wildcards>!?!?\??)(?P<multiplier>\d?\d?\d?)}')
    for i, c in enumerate(template):
        if c == '{':
            if not bracestack: # end of a regex section
                elements.append(('r', re.compile(template[regexstack.pop():i])))
            bracestack.append(i)
        if c == '}':
            start = bracestack.pop()
            if not bracestack: # end of placeholder
                _placeholder = placeholder.match(template[start:i+1]).groupdict()
                if _placeholder['subexpr'] == None:
                    _placeholder['subexpr'] = '.+?(?=\s|$)'
                elements.append(('p', _placeholder))
            # consider the text a regex until we encouter a new placeholder
            regexstack.append(i+1)
    if regexstack:
        elements.append(('r', re.compile(template[regexstack.pop():])))
    return elements
            


def match_template(template, text):
    attrs={"groups":[]}
    def match(template=template, text=text, start=0, subexpr=False, repeat_match=False):
        elements = indexed(template)
        for mark, element in elements:
            print(element, text[start:])
            if mark == 'r': # process as regex
                matches = []
                while True:
                    _match = element.match(text[start:])
                    if not _match:
                        return matches if repeat_match else None
                    start += _match.end(0)
                    grps = _match.groups()
                    if grps:
                        attrs['groups'].append(grps)
                    if repeat_match:
                        matches.append(_match.group(0))
                    elif subexpr:
                        return _match.group(0)
                    else:
                        break
            elif mark == 'p': #process as placeholder
                if '!' in element['wildcards']:
                    attrs[element['name']] = match(element['subexpr'], text, start, True, True)
                else:
                    attrs[element['name']] = match(element['subexpr'], text, start, True)
                start += len(attrs[element['name']])
    match()
    return attrs


        
template = 'TODO: {items!} {foo}'

print(match_template(template, "TODO: foobar baz fooo adawda"))

    











