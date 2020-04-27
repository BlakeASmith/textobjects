import re
from types import SimpleNamespace

PLACEHOLDER_START = '{'
PLACEHOLDER_END = '}'
PLACEHOLDER_PATTERN = re.compile(
        '{(?P<name>\w+)' 
        '<?(?P<subexpr>.*(?=>))?>?'
        '(?P<wildcards>!?!?\??)'
        '(?P<limit>\d?\d?\d?)}')

def parse_placeholder(placeholder):
    match = PLACEHOLDER_PATTERN.match(placeholder)
    _placeholder = SimpleNamespace(**match.groupdict())
    if not _placeholder.subexpr:
        _placeholder.subexpr = '\s*\S+?(?=\s|$)'
    return _placeholder

def addpattern(pattern, lst, placeholder=None):
    if pattern:
        lst.append((placeholder, re.compile(pattern)))

def parse(template):
    """produce a list of regex patterns associated with the
    appropriate placeholder information
    
    Args:
        template (str): the template string to parse

    Returns:
        a list of tuples (placeholder, pattern) where `placeholder`
        is a namespace with attributes name, subexpr, wildcards, limit
        and `pattern` is a compiled regex pattern or another list of
        tuples.

    """
    # TODO: escape sequences
    rstack, pstack, results = [0], [], []
    for i, c in enumerate(template):
        if c == PLACEHOLDER_START:
            if not pstack:
                addpattern(template[rstack.pop():i], results)
            pstack.append(i)
        if c == PLACEHOLDER_END:
            start = pstack.pop()
            if not pstack:
                placeholder = template[start:i+1]
                parsed = parse_placeholder(placeholder)
                if PLACEHOLDER_START in parsed.subexpr:
                    results.append((parsed, parse(parsed.subexpr)))
                else:
                    results.append((parsed, re.compile(parsed.subexpr)))
            rstack.append(i+1)

    addpattern(template[rstack.pop():i-1], results)

    return results

def wrap_and_match(func, pattern, placeholder, matchfun = lambda pat, text: pat.match(text)):
    if not isinstance(pattern, list):
        def match_placeholder(text, func=func):
            subtext, obj = func(text)
            match = matchfun(pattern, subtext)
            if not match:
                return (None, obj)
            setattr(obj, placeholder.name, match.group(0))
            return (subtext[match.end(0):], obj)
    else:
        def match_placeholder(text, func=func):
            subtext, obj = func(text)
            subsubtext, subobj = create_eval_function(pattern)(subtext)
            setattr(obj, placeholder.name, subobj)
            return (subsubtext, obj)
    return match_placeholder

def wrap_and_search(func, pattern, placeholder):
    if not isinstance(pattern, list):
        def search_placeholder(text, func=func):
            subtext, obj = func(text)
            match = pattern.search(subtext)
            setattr(obj, placeholder.name, match.group(0))
            if not match:
                return (None, obj)
            return (subtext[:match.start(0)] + subtext[match.end(0):], obj)
    else:
        def search_placeholder(text, func=func):
            subtext, obj = func(text)
            subsubtext, subobj = create_eval_function(pattern, search=True)(subtext)
            setattr(obj, placeholder.name, subobj)
            return (subsubtext, obj)
    return search_placeholder

def wrap_and_findall(func, pattern, placeholder):
    if not isinstance(pattern, list):
        def findall_placeholder(text, func=func):
            subtext, obj = func(text)
            matches = pattern.finditer(subtext)
            if not matches:
                return (None, obj)
            results = [m.group(0) for m in matches]
            for res in results:
                subtext = subtext.replace(res, '')
            setattr(obj, placeholder.name, results)
            return (subtext, obj)
    else:
        def findall_placeholder(text, func=func):
            subtext, obj = func(text)
            results = []
            returntext = text
            eval_func = create_eval_function(pattern, search=True)
            while True:
                subtext, subobj = eval_func(subtext)
                results.append(subobj)
                if not subtext:
                    break
                returntext = subtext
            setattr(obj, placeholder.name, results)
            return (returntext, obj)
    return findall_placeholder

def create_eval_function(parsed_template, func=lambda text: (text, SimpleNamespace()), search=False):

    def wrap_regex(func, pattern, matchfunc = lambda pat, text: pat.match(text)):
        def match_pattern(text, func=func, pattern=pattern):
            subtext, obj = func(text)
            match = matchfunc(pattern, subtext)
            if not match:
                return (None, obj)
            return (subtext[match.end(0):], obj)
        return match_pattern

    if search:
        placeholder, pattern = parsed_template[0]
        parsed_template = parsed_template[1:]

        def search_pattern(text, func=func):
            subtext, obj = func(text)
            if not isinstance(pattern, list):
                match = pattern.search(subtext)
                if not match:
                    return (None, obj)
                else:
                    if placeholder:
                        setattr(obj, placeholder.name, match.group(0))
                    return (subtext[match.end(0):], obj)

            searchmatches = pattern.finditer(subtext)
            fun = create_eval_function(parsed_template)
            result = None
            for match in searchmatches:
                result, subobj = fun(subtext[match.end(0):])
                if result:
                    return (subtext[match.end(0):], subobj)
            return (None, obj)
        func = search_pattern

    for placeholder, pattern in parsed_template:
        if placeholder:
            optional = '?' in placeholder.wildcards
            if '!!' in placeholder.wildcards:
                func = wrap_and_findall(func, pattern, placeholder)
            elif '!' in placeholder.wildcards:
                func = wrap_and_repeatmatch(func, pattern, placeholder)
            else:
                func = wrap_and_match(func, pattern, placeholder)
        else:
            func = wrap_regex(func, pattern)

    return func

    
if __name__ == '__main__':
    parsed = parse('TODO: {item<\w*,>!!}')
    # for var, pattern in parsed:
        # print(var, pattern)

    fun = create_eval_function(parsed)

    print(fun('TODO: item1, item2, [clearly not an item] item3'))
    
