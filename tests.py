from template import TemplateEvaluator
from unittest import main, TestCase

class TestWildcards(TestCase):
    # def testbasicmatch(self):
        # todo = TemplateEvaluator(strip_whitespace=True)('TODO: {item<.*$>}')
        # mytodo = todo('TODO: thing I want to do \n another line')
        # assert mytodo.item == 'thing I want to do'

    # def test_multiple_placeholders(self):
        # txtobj = TemplateEvaluator(strip_whitespace=True)(
                # '{first} {second} {third}')('first second third')
        # assert txtobj.first == 'first'
        # assert txtobj.second == 'second'
        # assert txtobj.third == 'third'

    # def test_capture_groups(self):
        # evaluator = TemplateEvaluator(capture_groups=(0, 1, 'date'))
        # datedtodo = evaluator.parse('TODO: {item<(.*)\s(?P<date>\d\d?/\d\d?/\d\d\d?\d?)>} ')
        # mytodo = datedtodo("TODO: don't get the corona 29/04/2020 ")
        # assert len(mytodo.item) == 3
        # assert mytodo.item[2] == '29/04/2020'

    # def test_recursive(self):
        # evaluator = TemplateEvaluator()
        # fun = evaluator.parse("{outer<foo{inner<~{word}~>}bar>}")
        # obj = fun("foo~something~bar")
        # assert obj.outer.inner.word == 'something'

    # def test_search(self):
        # fun = TemplateEvaluator().parse("{something} {outer<{bars<\|+>/} {between<.*>} {lyword<\w*ly>}>}")
        # obj = fun('something something else || other stuf sparcely')
        # assert obj.outer.lyword == 'sparcely'
        # assert obj.outer.bars == '||'

    def test_optional(self):
        fun = TemplateEvaluator(all_branches=True).parse('{optional<{two<{three?}>}>?} {foo} {bar}')
        obj1 = fun(' foo bar')
        print(obj1)
        assert obj1.optional == None
        assert obj1.foo == 'foo'
        assert obj1.bar == 'bar' 
        obj2 = fun('two foo bar')
        print(obj2)
        assert obj2.optional.two.three == 'two'
        assert obj2.foo == 'foo'
        assert obj2.bar == 'bar'

if __name__ == '__main__':
    main() 
