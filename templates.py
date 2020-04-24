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


class TextNode(NodeMixin):
    """A Node which contains a substring of a larger body of text"""
    def __init__(self, text=None, parent=None, children=None):
        self.text = text
        self.parent = parent
        if children:
            self.children = children

    def __init_subclass__(cls, outer_text, *args, **kwargs):
        super(TextNode, cls).__init_subclass__(*args, **kwargs)
        cls.outer_text = outer_text


    def __str__(self):
        return self.text

    def __repr__(self):
        return self.text


def iswildcard(char):
    return (char == '!' or char == '?' or isdigit(char))

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

def expanded(s):
    # print(s)
    exp = re.sub('{(\w*?)}', '(?P<\g<1>>.*?(?=\\\\s))', s) 
    exp = re.sub('{(\w*)<(.*?)>!?!?\??}', '(?P<\g<1>>\g<2>)', exp)
    # print(exp, '\n')
    return exp

def expand(root):
    if not root.children:
        return expanded(root.text)
    for child in root.children:
        root.text = expanded(root.text.replace(child.text, expand(child)))
    return root.text


root = build_tree(r"""
{line1<^{word1} {word99} {word3}$>!}
""")

# print(RenderTree(root))

regex = expand(root)
print(regex)
print(re.compile(regex).groupindex)

print(re.match(regex, """
foo bar baz 
baz cat bush 
fibonachi potato peeler 
fibonachi potato peeler 
fibonachi potato peeler""", re.M).groupdict())








