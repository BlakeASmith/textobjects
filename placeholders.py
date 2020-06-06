"""placeholders for template strings"""
import re
from dataclasses import dataclass
from typing import Iterable
from abc import ABC, abstractproperty, abstractclassmethod

PLACEHOLDER_START = '<'
"""The start symbol for a Placeholder"""
PLACEHOLDER_END = '>'
"""The terminating symbol for a Placeholder"""

PLACEHOLDER_PATTERN = r"<(?P<name>\w+):?(?P<subexpr>.*?(?=:|>)):?(?P<wildcards>.*?):?(?P<limit>\d*?)>"
"""The pattern used to extract Placeholders from the template"""

# PLACEHOLDER_PATTERN = re.compile(
        # '{(?P<name>\w+)' 
        # '(<(?P<subexpr>.*(?=>))>)?'
        # '(?P<wildcards>\D*)'
        # '(?P<limit>\d?\d?\d?)}')

DEFAULT_PLACEHOLDER_SUBEXPR = '\w+'
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
    parent: 'Placeholder' = None
    """The parent placeholder"""

