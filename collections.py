import time
import collections
import textobjects
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# 1. collect the textobjects from the text
# 2. make changes to those text objects
# 3. repeatedly search for the textobjects and replace them with their associated values

class Page(collections.abc.MutableSequence):
    """A block of text which contains other TextObjects"""
    def __init__(self, text, *textobjects, find=textobjects.findall):
        self.data = text
        self.types = textobjects
        self.find = find
        self.__objects = self.__search_text()

    def __str__(self):
        return self.data

    def __search_text(self):
        objects = []
        for typ in self.types:
            found = self.find(typ, self.data)
            objects.extend(found)
        objects.sort(key=lambda it: it.start)
        return objects

    def __getitem__(self, key):
        return self.__objects[key]

    def __setitem__(self, key, value):
        self.__objects[key] = value

    def __delitem__(self, key):
        self[key] = None

    def insert(self, key, value):
        self.__objects.insert(key, value)

    def __len__(self):
        return len(self.__objects)

    def pop(self, index=None):
        """Since the length of this collection should not decrease pop needs
        to ignore None values"""
        ind = index if index else -1
        while not self[ind]:
            ind -= 1
        del self[ind]

    def write(self):
        """apply the changes in this collection to the text, subsituting each of the values
        with it's associated new value"""
        objects = self.__search_text()
        offset = 0
        while len(objects) > len(self): # items were removed
            self.insert(0, None) 
        for old, new in zip(objects, self):
            if not new:
                new = ''
            self.data = self.data[:old.start+offset] + str(new) + self.data[old.end+offset:]
            offset += len(new) - len(old)
        j = len(objects)
        while j < len(self): # items were added
            self.text = self.text.strip() + '\n' + str(self[j])
            j += 1
            
        

