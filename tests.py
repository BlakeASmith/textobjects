import re
import time
import textobjects.template as template
from textobjects import storage
import textobjects
from unittest import main, TestCase

class TestWildcards(TestCase):
    def testbasicmatch(self):
        todo  = template.evaluate('TODO: {item<.*$>}')
        mytodo = todo('TODO: thing I want to do \n another line')
        assert mytodo.item == 'thing I want to do'

    def test_multiple_placeholders(self):
        txtobj = template.evaluate(
                '{first} {second} {third}')('first second third')
        assert txtobj.first == 'first'
        assert txtobj.second == 'second'
        assert txtobj.third == 'third'

    def test_capture_groups(self):
        datedtodo = template.evaluate('TODO: {item<(.*)\s(?P<date>\d\d?/\d\d?/\d\d\d?\d?)>}', 
                template.Options(capture_groups=(0, 1, 'date')))
        mytodo = datedtodo("TODO: don't get the corona 29/04/2020 ")
        assert len(mytodo.item) == 3
        assert mytodo.item[2] == '29/04/2020'

    def test_recursive(self):
        fun = template.evaluate("{outer<foo{inner<~{word}~>}bar>}")
        obj = fun("foo~something~bar")
        assert obj.outer.inner.word == 'something'

    def test_search(self):
        fun = template.evaluate("{something} {outer<{bars<\|+>/} {between<.*>} {lyword<\w*ly>}>}")
        obj = fun('something something else || other stuf sparcely')
        assert obj.outer.lyword == 'sparcely'
        assert obj.outer.bars == '||'

    def test_optional(self):
        fun = template.evaluate('{optional<{two<{three}>}>?} {foo} {bar}',
                template.Options(strict_whitespace=True))
        obj1 = fun('foo bar')
        assert obj1.optional == None
        assert obj1.foo == 'foo'
        assert obj1.bar == 'bar' 
        obj2 = fun('two foo bar')
        assert obj2.optional.two.three == 'two'
        assert obj2.foo == 'foo'
        assert obj2.bar == 'bar'

    def test_all_matches(self):
        evaluate = template.evaluate('{word1} {word2?} {word3?} {word4}', 
                template.Options(all_matches=True))
        objs = evaluate('four optional words')
        assert len(objs) == 4
    
    def test_repeat_match(self): 
        evaluator = template.evaluate('{word1} {foos<\s*foo>!} {word2}')
        obj = evaluator('word1 foo foo foo foo foo word2')
        assert len(obj.foos) == 5

    def test_loose_repeat_match(self):
        evaluate = template.evaluate('{word1} {foos<foo>~!} {word2}')
        obj = evaluate('word1 foo | foo | foo | foo | not a foo | foo word2')
        assert len(obj.foos) == 6

class TextStorage(TestCase):
    def test_mappings(self):
        ToDo = textobjects.create('ToDo', '^#TODO: {item<.+>}$')
        store = storage.TextObjectStorage([ToDo], 'textobjects/storage.py')
        class Observer(storage.TextObjectObserver):
            def on_textobject_added(self, txtobj):
                print(txtobj, 'was added')
            def on_textobject_removed(self, txtobj):
                print(txtobj, 'was removed')

        store.subscribe(Observer())
        store += ['#TODO: 7', '#TODO: 2']
        store.clear()



if __name__ == '__main__':
    main() 
