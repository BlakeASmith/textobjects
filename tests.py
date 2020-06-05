import re
import time
import string
import random
import textobjects
from textobjects import regex
from textobjects.textobject import textobjecttypes
from pathlib import Path
from unittest import main, TestCase

def test_regex_textobject():
    Foo = textobjects.create('Foo', 'foo<bar:cat>')
    print(Foo("foocat"))

test_regex_textobject()

