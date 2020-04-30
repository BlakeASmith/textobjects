"""Parse template strings to create evaluator functions"""
import re
from wildcards import Wildcard
from placeholders import *
from typedef import EvaluationContext, ExecutionContext, Options
from types import SimpleNamespace
from functools import wraps
from dataclasses import dataclass
from collections.abc import Iterable


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

class TemplateEvaluator:
    """interpret placeholder strings to pull data from text

    Args: 
        **kwargs: options for parsing and evaluating the template.
            all keyword arguments will be passed to the constructor 
            of :py:class:`typedef.options` like this:

                typedef.Options(**kwargs)            
    """
    def __init__(self, **kwargs):
        self.options = Options(**kwargs)

    def __addpattern(self, pattern, lst, placeholder=None):
        if pattern:
            lst.append((placeholder, re.compile(pattern, *self.options.re_flags)))

    def __parse(self, template: str):
        """produce a list of Patterns associated with the
        appropriate placeholder information
        
        Args:
            template (str): the template string to parse

        Returns:

        (ParsedTemplate):
            each Placeholder in the template assocated to it's pattern"""
        rstack, pstack, results = [0], [], []
        for i, c in enumerate(template):
            if c == PLACEHOLDER_START:
                if not pstack:
                    self.__addpattern(template[rstack.pop():i], results)
                pstack.append(i)
            if c == PLACEHOLDER_END:
                start = pstack.pop()
                if not pstack:
                    placeholder = template[start:i+1]
                    parsed = parse_placeholder(placeholder)
                    if PLACEHOLDER_START in parsed.subexpr:
                        results.append((parsed, self.__parse(parsed.subexpr)))
                    else:
                        self.__addpattern(parsed.subexpr, results, parsed)
                rstack.append(i+1)

        self.__addpattern(template[rstack.pop():], results)
        return results

    def __adjust_by_future(self, parsedtemplate):
        for i, (placeholder, pattern) in enumerate(parsedtemplate[:-1]):
            if isinstance(pattern, list):
                parsedtemplate[i] = (placeholder, self.__adjust_by_future(pattern))
            else:
                if placeholder:
                    patt = parsedtemplate[i+1][1].pattern
                    lookahead = f'(?={patt})'
                    newpatt = re.compile(pattern.pattern+lookahead, *self.options.re_flags)
                    parsedtemplate[i] = (placeholder, newpatt)


        return parsedtemplate


    def parse(self, template: str, rec=False):
        """evaluate the Template

        Args:
            template (str): the template string to parse

        Returns:
            (Callable[[str], SimpleNamespace]):
            a function to produce an object containing 
            attributes for any placeholders in the template
        """
        def func(text):
            ctx = ExecutionContext(text=text, remaining_text=text, 
                    consumed_text='', options=self.options)
            return (ctx, SimpleNamespace())

        parsedtemplate = self.__parse(template) if not rec else template
        parsedtemplate = self.__adjust_by_future(parsedtemplate) 
        for placeholder, pattern in parsedtemplate:
            context = EvaluationContext(func, placeholder, pattern, self)
            if placeholder:
                for wildcard in placeholder.wildcards:
                    func = wildcard(context)
            else: 
                func = Wildcard.default_transformation(context)

        if rec:
            return func

        @wraps(func)
        def wrapper(text):
            ctx, result = func(text)
            return result
        return wrapper

    def __call__(self, template: str):
        return self.parse(template)



