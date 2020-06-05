"""a simple regex implementation of textobject templates"""
import re
from textobjects import textobject, placeholders

class RegexTextObject(textobject.StructuredText):
    def __init_subclass__(cls, regex, *args, **kwargs):
        cls.pattern = re.compile(regex)

    def __new__(cls, text):
        return cls.__match__(text)

    def __init__(self, text):
        pass

    @classmethod
    def __match__(cls, text):
        m = cls.pattern.match(text)
        to = object.__new__(cls)
        super(RegexTextObject, to).__init__(m.group(0), text, m.start(), m.end())
        for key, val in m.groupdict().items():
            setattr(to, key, val)
        to.others = m.groups()
        return to

    @classmethod
    def __search__(cls, text):
        m = cls.pattern.search(text)
        to = super(RegexTextObject).__new__(m.group(0), text, m.start(), m.end())
        for key, val in m.groupdict().items():
            setattr(to, key, val)
        to.others = m.groups()
        return to

    @classmethod
    def __findall__(cls, text):
        matches = cls.pattern.finditer(text)
        to_list = []
        for m in matches:
            to = super(RegexTextObject).__new__(m.group(0), text, m.start(), m.end())
            for key, val in m.groupdict().items():
                setattr(to, key, val)
            to.others = m.groups()
            to_list.append(to.others)
        return to_list

def parse(name, template):
    _placeholders = re.finditer(placeholders.PLACEHOLDER_PATTERN, template)
    for ph in _placeholders:
        groups = ph.groupdict()
        if groups['wildcards'] or groups['limit']:
            raise NotImplementedError("wildcard modifiers are not implemented for regex textobjects")
        expr = groups['subexpr'] or placeholders.DEFAULT_PLACEHOLDER_SUBEXPR
        template = template.replace(ph.group(0), f'(?P<{groups["name"]}>{expr})')

    class Temp(RegexTextObject, regex=template): ...
    Temp.__name__ = Temp.__qualname__ = name
    return Temp


