"""Parse template strings to create evaluator functions"""
import re
from types import SimpleNamespace
from dataclasses import dataclass
from typing import Callable, Iterable, Any, Literal
from functools import wraps

# TODO: add support for escaping `{` and `}`
# TODO: get -> to work with ! and !!
# TODO: get ? to work with other wildcards
# TODO: refactor wrapping functions 

PLACEHOLDER_START = '{'
PLACEHOLDER_END = '}'
PLACEHOLDER_PATTERN = re.compile(
        '{(?P<name>\w+)' 
        '(<(?P<subexpr>.*?(?=>))>)?'
        '(?P<wildcards>\D*)'
        '(?P<limit>\d?\d?\d?)}')
DEFAULT_PLACEHOLDER_SUBEXPR = '\s*\S+?(?=\s|$)'

@dataclass
class Placeholder:
    """a template string placeholder"""
    name: str
    subexpr: str = DEFAULT_PLACEHOLDER_SUBEXPR
    """the subexpression of the placeholder, it can be any
    arbitrary template string. Whatever text matches this expression
    will be stored"""
    wildcards: Iterable[str] = None
    """the wildcards applied to this placeholder """
    limit: int = 0
    """the maximum number of times to apply any of the wildcards"""

@dataclass
class ExecutionContext:
    text: str

@dataclass
class EvaluationContext:
    func: Callable[[str], ExecutionContext]
    placeholder: Placeholder
    pattern: Any

REPEAT_WILDCARD = '!'
LOOSE_REPEAT_WILDCARD = '!!'
OPTIONAL_WILDCARD = '?'
LOOSE_MATCH_WILDCARD = '->'

def wrap_and_match(ctx):
    """match the pattern from the evaluation context and 
    store it in the placeholder variabld"""
    if not isinstance(ctx.pattern, list):
        def match_placeholder(text, func=ctx.func):
            context, obj = func(text)
            match = ctx.pattern.match(context.text)
            if not match:
                raise ValueError(f'{context.text} does not match {ctx.pattern.pattern}')
            if ctx.placeholder:
                setattr(obj, ctx.placeholder.name, match.group(0))
            context.text = context.text[match.end(0):]
            return (context, obj)
    else:
        def match_placeholder(text, func=ctx.func):
            context, obj = func(text)
            subcontext, subobj = create_eval_function(ctx.pattern)(context.text)
            if ctx.placeholder:
                setattr(obj, ctx.placeholder.name, subobj)
            return (subcontext, obj)
    return match_placeholder

def wrap_and_repeatmatch(ctx):
    if not isinstance(ctx.pattern, list):
        def repeatmatch_placeholder(text, func=ctx.func, pattern=ctx.pattern, placeholder=ctx.placeholder):
            context, obj = func(text)
            results, subtext, count = [], context.text, 0
            while True:
                match = pattern.match(subtext)
                if not match or count == placeholder.limit:
                    break
                count += 1
                subtext = subtext[match.end(0):]
                results.append(match.group(0))
            setattr(obj, placeholder.name, results)
            context.text = subtext
            return (context, obj)
    else:
        def repeatmatch_placeholder(text, func=func, ctx=ctx):
            context, obj = func(text)
            fun = create_eval_function(pattern)
            returntext = context.text
            results = []
            while True:
                try:
                    subcontext, subobj = fun(context.text)
                    if subtext:
                        returntext = subcontext.text
                        results.append(subobj)
                except:
                    break
            setattr(obj, ctx.placeholder.name, results)
            context.text = returntext
            return (context, obj)
    return repeatmatch_placeholder

def wrap_and_findall(ctx):
    func, pattern, placeholder = ctx.func, ctx.pattern, ctx.placeholder
    if not isinstance(pattern, list):
        def findall_placeholder(text, func=func):
            context, obj = func(text)
            matches = pattern.finditer(context.text)
            if not matches:
                raise ValueError("{context.text} does not match {pattern.pattern}")
            results = [m.group(0) for m in matches]
            for res in results:
                context.text = context.text.replace(res, '')
            results = results[:min(len(results), placeholder.limit)]
            setattr(obj, placeholder.name, results)
            return (context, obj)
    else:
        def findall_placeholder(text, func=func):
            context, obj = func(text)
            results, returntext = [], context.text
            eval_func = create_eval_function(pattern, search=True)
            while True:
                subcontext, subobj = eval_func(subtext)
                results.append(subobj)
                if not subcontext.text:
                    break
                returntext = subtext
            setattr(obj, placeholder.name, results)
            return (returntext, obj)
    return findall_placeholder

def wrap_optional(ctx):
    pass

def wrap_search(ctx):
    def search_pattern(text, func=ctx.func, pattern=ctx.pattern, placeholder=ctx.placeholder):
        context, obj = func(text)
        subtext = context.text
        if not isinstance(pattern, list):
            match = pattern.search(subtext)
            if not match:
                raise ValueError(f"could not find {pattern.pattern} in {subtext}")
            context.text = subtext[match.end(0):]
            if placeholder:
                setattr(obj, placeholder.name, match.group(0))
            return (context, obj)

        searchmatches = pattern[0][1].finditer(subtext)
        fun = create_eval_function(pattern[1:])
        result = None
        for match in searchmatches:
            try:
                subcontext, subobj = fun(context.text[match.end(0):])
                return (subcontext, subobj)
            except:
                pass
        raise ValueError(f"search failed")
    return search_pattern

WILDCARD_MAP = {
        LOOSE_REPEAT_WILDCARD:wrap_and_findall,
        REPEAT_WILDCARD:wrap_and_repeatmatch,
        OPTIONAL_WILDCARD:wrap_optional,
        LOOSE_MATCH_WILDCARD:wrap_search
}

def parse_placeholder(placeholder: str):
    """extract name, expression, and wildcards from the text of a placeholder
    
    Args:
        placeholder (str): the string representing the placeholder

    Returns:
        a ~template.Placeholder
    """
    match = PLACEHOLDER_PATTERN.match(placeholder).groupdict()

    return Placeholder(
            name = match['name'], 
            subexpr = match['subexpr'] if match['subexpr'] else DEFAULT_PLACEHOLDER_SUBEXPR,
            wildcards = re.findall("|".join(WILDCARD_MAP).replace('?', '\?'), match['wildcards']),
            limit = int(match['limit']) if match['limit'] else None)

def __addpattern(pattern, lst, placeholder=None):
    if pattern:
        lst.append((placeholder, re.compile(pattern)))

def parse(template: str):
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
    rstack, pstack, results = [0], [], []
    for i, c in enumerate(template):
        if c == PLACEHOLDER_START:
            if not pstack:
                __addpattern(template[rstack.pop():i], results)
            pstack.append(i)
        if c == PLACEHOLDER_END:
            start = pstack.pop()
            if not pstack:
                placeholder = template[start:i+1]
                parsed = parse_placeholder(placeholder)
                if PLACEHOLDER_START in parsed.subexpr and PLACEHOLDER_END in parsed.subexpr:
                    results.append((parsed, parse(parsed.subexpr)))
                else:
                    results.append((parsed, re.compile(parsed.subexpr)))
            rstack.append(i+1)

    __addpattern(template[rstack.pop():i-1], results)
    return results

def wrap_wildcards(ctx):
    func = ctx.func 
    for wc in ctx.placeholder.wildcards:
        func = WILDCARD_MAP[wc](ctx)
    return func

def create_eval_func(parsed_template, func=lambda text: (SimpleNamespace(text=text), SimpleNamespace())):
    for placeholder, pattern in parsed_template:
        ctx = EvaluationContext(func, placeholder, pattern)
        if placeholder and placeholder.wildcards:
            func = wrap_wildcards(ctx)
        else:
            func = wrap_and_match(ctx)

    return func

def evaluate(template: str):
    """evaluate the template string

    Args:
        template (str): the template string

    Returns:
        a function which takes a block of text as an argument and 
        returns an object with attributes specified by the 
        placeholders in the template
    """
    func = create_eval_func(parse(template))

    @wraps(func)
    def wrapper(text):
        ctx, result = func(text)
        return result
    return wrapper


if __name__ == '__main__':
    fun = evaluate('TODO: {item<.*>->}')
    print(fun('TODO:  item1 item2 [clearly [not an item] [item3]'))
    
