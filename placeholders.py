"""placeholders for template strings"""
import re
from dataclasses import dataclass
from typing import Iterable


PLACEHOLDER_START = '{'
"""The start symbol for a Placeholder"""
PLACEHOLDER_END = '}'
"""The terminating symbol for a Placeholder"""

PLACEHOLDER_PATTERN = re.compile(
        '{(?P<name>\w+)' 
        '(<(?P<subexpr>.*?(?=>))>)?'
        '(?P<wildcards>\D*)'
        '(?P<limit>\d?\d?\d?)}')
"""The pattern used to extract Placeholders from the template"""

DEFAULT_PLACEHOLDER_SUBEXPR = '\s*\S+?(?=\s|$)'
"""The pattern to be substituted when no pattern is specified for the placeholder eg. (**{name}**)"""

@dataclass
class Placeholder:
    """a template string placeholder"""
    name: str
    subexpr: str = DEFAULT_PLACEHOLDER_SUBEXPR
    """the subexpression of the placeholder, it can be any
    arbitrary template string. Whatever text matches this expression
    will be stored"""
    wildcards: Iterable = None
    """the wildcards applied to this placeholder """
    limit: int = 0
    """the maximum number of times to apply any of the wildcards"""

