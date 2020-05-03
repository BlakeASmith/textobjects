import re
from abc import ABC
from typing import Union, List, Mapping, Optional

class Match(ABC):
    """emulate re.MatchObject"""
    @abstractmethod
    def start(group: Union[str, int]) -> int:
        pass

    @abstractmethod
    def end(group: Union[str, int]) -> int:
        pass

    @abstractmethod
    def span(group: Union[str, int]) -> int:
        pass

    @abstractmethod
    def group(*groups: Union[str, int]) -> Union[List[str], str]:
        pass

    @abstractmethod
    def groups() -> List[str]:
        pass

    @abstractmethod
    def groupdict() -> Mapping[Union[str, int], str]:
        pass

class RegexMatch(Match):
    """wrapper around re.MatchObject"""
    def __init__(self, match):
        self.match = match

    def start(group=0):
        return self.match.start(group)

    def end(group=0):
        return self.match.end(group)

    def span(group=0):
        return self.match.span(group)

    def group(group):
        return self.match.group(group)

    def groups():
        return self.match.groups()

    def groupdict():
        return self.match.groupdict()

class TemplateMatch(Match):


class Pattern(ABC):
    """emulate re.RegexObject"""
    @abstractmethod
    def match(text: str) -> Optional[Match]
        pass

    @abstractmethod
    def search(text: str) -> Optional[Match]
        pass

    @abstractmethod
    def findall(text: str) -> List[Match]
        pass



class Template(Pattern):
    pass


if __name__ == '__main__':
    Template()
