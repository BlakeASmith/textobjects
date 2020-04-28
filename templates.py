import re
from types import SimpleNamespace
from functools import partial, wraps

def match(text, expression, optional=False):
    _match = expression.match(text)
    if _match:
        subtext, matchtext = text[_match.end(0):], _match.group(0)
    elif optional:
        subtext, matchtext = text, None
    else:
        subtext, matchtext = None, None
    return (subtext, matchtext)

def repeat_match(text, expression,  optional=False, limit=None):
    subtext = returntext = text
    matches, counter = [], 0
    while True:
        subtext, matchtext = match(expression, subtext, optional)
        counter += 1
        if subtext:
            returntext = subtext
        if counter == limit:
            return (returntext, matchtext)
        if matchtext:
            matches.append(matchtext)
            continue
        break
    return (returntext, matches)

def repeateval(text, template, func, optional=False):
    results, remaining = [], func(text)
    while True:
        returntext = remaining
        try:
            result, fun = evaluate(template, rec=True)
            remaining = fun(remaining)
            results.append(result)
            if not remaining or returntext == remaining:
                return (returntext, results)
        except: #did not match
            return (remaining, results)

def findall(text, template, func, optional=False, limit=None):
    results, counter = [], 0
    remaining = returntext = beforetext = func(text)
    while remaining:
        counter += 1
        if counter == limit:
            break
        result, fun = evaluate(template, rec=True)
        remaining = fun(remaining)
        returntext = ''.join([c for c, cc in zip(reversed(remaining), reversed(beforetext[:len(remaining)])) if c == cc])
        results.append(result)
        if remaining == beforetext: 
            remaining = remaining[1:]
            beforetext = remaining
    return (results, returntext)


class Placeholder:
    def __init__(self, name=None, subexpr=None,  wildcards=None, limit=None, parent=None):
        self.name, self.subexpr, self.wildcards, self.limit = name, subexpr, wildcards, limit
        self.parent = parent
        self.type = 'p'

    def __str__(self):
        return str(self.name)

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
                _placeholder = Placeholder(**placeholder.match(template[start:i+1]).groupdict(), parent=parent)
                _placeholder.subexpr = _placeholder.subexpr if _placeholder.subexpr else '\s*\S+?(?=\s|$)'
                elements.append(_placeholder)
            # consider the text a regex until we encouter a new placeholder
            if not bracestack:
                regexstack.append(i+1)
    addregex(len(template))
    return elements

def evalwildcards(wildcards, limit, template = None, func=None):
    if wildcards:
        optional = '?' in wildcards
        if '{' in template:
            if '!!' in wildcards:
                evalscheme = partial(findall, template=template, func=func, optional=optional)
            elif '!' in wildcards:
                evalscheme = partial(repeateval, template=template, func=func, optional=optional)
        elif '!!' in wildcards:
            evalscheme = partial(findall, template=template, func=func, optional=optional, limit=limit)
        elif '!' in wildcards:
            evalscheme = partial(repeat_match, optional=optional, limit=limit)
        else:
            evalscheme = partial(match, optional=False)
    else:
        evalscheme = partial(match, optional=False)


    return evalscheme

def evaluate(template, rec=False):
    all_attrs = {}
    def _evaluate(template, attrs,  placeholder=Placeholder(), func=lambda text: text):
        evalscheme = evalwildcards(placeholder.wildcards, placeholder.limit, template, func)    

        # basecase, just a regex pattern
        if '{' not in template:
            def evalpattern(text, func=func , attrs=attrs):
                newtext, match = evalscheme(func(text), re.compile(template))
                if placeholder.name:
                    attrs[placeholder.name] = match

                return newtext
            return evalpattern


        for element in split_regex_and_placeholders(template, parent=placeholder):
             if element.type == 'p': # `pattern` is a placeholder
                if placeholder.name not in attrs:
                    attrs[placeholder.name] = {}
                if evalscheme == findall or evalscheme == repeateval:
                    def wrapper(text, func=func):
                        newtext, matches = evalscheme(func(text))
                        if placeholder.name:
                            attrs[placeholder.name] = matches
                        return newtext
                    func = wrapper
                else:
                    func = _evaluate(element.subexpr, attrs[placeholder.name], element, func)
             else: # `element` is a regex and is part of some placeholder
                def evalpattern(text, func=func, pattern=element.pattern, attrs=attrs):
                    newtext, match = evalscheme(func(text), expression=re.compile(pattern))
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


func = evaluate("TODO: {foo}!!")
print(func("TODO: ~~foo fob~~ ~~fo sh cat~~  stuff that is nti un  ~~barrrr~~ "))










