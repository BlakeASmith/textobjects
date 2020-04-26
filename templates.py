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
from types import SimpleNamespace
from functools import partial, wraps

def match(expression, text, optional=False):
    _match = expression.match(text)
    if _match:
        subtext, matchtext = text[_match.end(0):], _match.group(0)
    elif optional:
        subtext, matchtext = text, None
    else:
        subtext, matchtext = None, None
    return (subtext, matchtext)

def repeat_match(expression, text, optional=False, limit=None):
    subtext = returntext = text
    matches = []
    while True:
        subtext, matchtext = match(expression, subtext, optional)
        if subtext:
            returntext = subtext
        if matchtext:
            matches.append(matchtext)
            continue
        break
    return (returntext, matches)

def findall(expression, text, optional=False, limit=None):
    print(findall, text, optional, limit, expression)
    return text

class Placeholder:
    def __init__(self, name=None, subexpr=None,  wildcards=None, limit=None, parent=None):
        self.name, self.subexpr, self.wildcards, self.limit = name, subexpr, wildcards, limit
        self.parent = parent

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return str(self)

def split_regex_and_placeholders(template, parent=None):
    """separate the regex and placeholder sections of the template"""
    elements, regexstack, bracestack = [], [0], []
    placeholder = re.compile(
            '{(?P<name>\w+)' 
            '<?(?P<subexpr>.*(?=>))?>?'
            '(?P<wildcards>!?!?\??)'
            '(?P<limit>\d?\d?\d?)}')

    def addregex(end):
        if regexstack:
            patt = template[regexstack.pop():end]
            if patt:
                elements.append(SimpleNamespace(type='r',pattern=re.compile(patt)))

    for i, c in enumerate(template):
        if c == '{':
            if not bracestack: # end of a regex section
                addregex(i)
            bracestack.append(i)
        if c == '}':
            start = bracestack.pop()
            if not bracestack: # end of placeholder
                _placeholder = Placeholder(**placeholder.match(template[start:i+1]).groupdict())
                _placeholder.parent = parent
                _placeholder.subexpr = _placeholder.subexpr if _placeholder.subexpr else '\s*\S+?(?=\s|$)'
                _placeholder.type = 'p'
                elements.append(_placeholder)
            # consider the text a regex until we encouter a new placeholder
            if not bracestack:
                regexstack.append(i+1)
    addregex(len(template))
    return elements

def evalwildcards(wildcards, limit):
    if wildcards:
        optional = '?' in wildcards
        if '!!' in wildcards:
            evalscheme = partial(findall, optional=optional, limit=limit)
        elif '!' in wildcards:
            evalscheme = partial(repeat_match, optional=optional, limit=limit)
        else:
            evalscheme = partial(match, optional=False)
    else:
        evalscheme = partial(match, optional=False)

    return evalscheme

def evaluate(template, rec=False):
    def func(text):
        return text

    all_attrs = {}
    def _evaluate(template, attrs,  placeholder=Placeholder(), func=func, lvl=0):
        evalscheme = partial(match, optional=False)
        evalscheme = evalwildcards(placeholder.wildcards, placeholder.limit)    
        if placeholder.wildcards:
            if '!' in placeholder.wildcards and '{' in template:
                def repeateval(text, *args, **kwargs):
                    results = []
                    remaining = text
                    while True:
                        returntext = remaining
                        try:
                            result, fun = evaluate(template, rec=True)
                            remaining = fun(remaining)
                            results.append(result)
                            if not remaining:
                                return (returntext, results)
                        except:
                            print(template)
                            return (remaining, results)
                    
                evalscheme = repeateval

        elements = split_regex_and_placeholders(template, parent=placeholder)
        for element in elements:
            if element.type == 'p': # `pattern` is a placeholder
                if placeholder.name not in attrs:
                    attrs[placeholder.name] = {}
                func =  _evaluate(element.subexpr, attrs[placeholder.name], element, func, lvl+1)

            elif element.type == 'r': # `pattern` is a regex
                @wraps(func)
                def evalpattern(text, func=func, pattern=element.pattern, attrs=attrs):
                    newtext, match = evalscheme(expression=pattern, text=func(text))
                    if placeholder.name:
                        if len(elements) == 1 or type(match) is list:
                            attrs[placeholder.name] = match

                    return newtext
                func = evalpattern
            
        return func

    def _func(text):
        remaining = _evaluate(template, attrs=all_attrs)(text)
        return all_attrs[None]
    if not rec:
        return _func
    else:
        func = _evaluate(template, attrs=all_attrs)
        return (all_attrs[None], func)


func = evaluate("TODO: {word<{foo} {bar!} {cat}>}")
print(func("TODO: foo fob fo fish cat  barrrr "))










