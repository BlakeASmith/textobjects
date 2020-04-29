"""Parse template strings to create evaluator functions"""
import re
from wildcards import Wildcard
from placeholders import *
from typedef import EvaluationContext, ExecutionContext, ParsedTemplate
from types import SimpleNamespace
from functools import wraps


def parse_placeholder(placeholder:str):
    """extract name, expression, and wildcards from the text of a placeholder
    
    Args:
        placeholder (str): the string representing the placeholder

    Returns:
        (placeholders.Placeholder): A Placeholder from the string
    """
    match = PLACEHOLDER_PATTERN.match(placeholder).groupdict()

    return Placeholder(
            name = match['name'], 
            subexpr = match['subexpr'] if match['subexpr'] else DEFAULT_PLACEHOLDER_SUBEXPR,
            wildcards = Wildcard.parse(match['wildcards']),
            limit = int(match['limit']) if match['limit'] else None)

def __addpattern(pattern, lst, placeholder=None):
    if pattern:
        lst.append((placeholder, re.compile(pattern)))
def parse(template: str):
    """produce a list of Patterns associated with the
    appropriate placeholder information
    
    Args:
        template (str): the template string to parse

    Returns:

    (ParsedTemplate):
        each Placeholder in the template assocated to it's pattern

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

def create_eval_func(parsed_template, func=lambda text: (SimpleNamespace(text=text), SimpleNamespace())):
    """Apply all TemplateTransformations specified by the wildcards for each Placeholder, TemplatePattern pair
    in the parsed template """
    for placeholder, pattern in parsed_template:
        context = EvaluationContext(func, placeholder, pattern)
        if placeholder:
            for wildcard in placeholder.wildcards:
                func = wildcard(context)
        else: 
            func = Wildcard.default_transformation(context)
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
    fun = evaluate('TODO: {item}')
    print(fun('TODO:  item1 item2 [clearly [not an item] [item3]'))
    
