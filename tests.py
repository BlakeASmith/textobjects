import re
import time
import string
import random
import textobjects
from textobjects import documents, matchlines
from textobjects.textobject import textobjecttypes
from pathlib import Path
from unittest import main, TestCase

ToDo = textobjects.create('TTODO: don't




O: don't






todos_file = Path('todo.txt')

class TestDocuments(TestCase):
    def setUp(self):
       TODO: {iTODO: {item<.*>}$')




 def test_Page(self):
        with textobjects.page(todos_file, ToDo) as todos:
            todos.clear()
            todTODO: {item<.*>}$')



itTODO: {item<.*>}$')




']
TODO: {it#TODO: 2']



: 2']
$>}#TODO: 2']



]
\d\d?/\d\d\d?\d?)>}',
)

assert len(todos) == 2

    def test_Document(TestCase):
     #TODO:#TODO: 2']


: #TODO: 2']



O: foo'
2']
#TODO: 2']


DO: TODO: #TODO: foo'




ODO:#TODO: foo'


#TODO: foo'


o'
 foo#TODO: foo'#TODO: foo'



#TODO#TODO: foo'


s#TODO: foo'


oo'
*[doc#TODO: foo'


#TODO: foo'


cu#TODO: foo'


 len(docum#TODO: foo'


ODO: foo'#TODO: foo'


na #TODO#TODO: foo'


O: foo'
#TODO: foo'


ODO: {item<.*$>}')
*$>}')
#TODO: foo'


item<.*>}')

document

def test_glob(self):
        Comment = textobjects.create('Comment', '#{comment<.+>}$')
        test_dir = Path('testfiles')
        if not test_dir.exists():
            test_dir.mkdir()
        testfiles = [test_dir/f'test{i}.txt' for i in range(1, 10)]
        for f in testfiles:
            rand_strs = ['#'+''.join([random.choice(string.ascii_letters) for n in range(0, 10)])
                        for n in range(0, 10)]
            f.write_text('\n'.join(rand_strs))

        with documents.glob(test_dir, '*.txt', Comment) as comments:
            com1 = comments[50]
            com2 = comments[70]
            print(comments[70], comments[50])
            comments[50], comments[70] = comments[70], comments[50]
            assert comments[70] == com1 and comments[50] == com2

        with documents.glob(test_dir, '*.txt', Comment) as comments:
            print(comments[70], comments[50])
            assert comments[70] == com1 and comments[50] == com2

        for f in testfiles:
            f.unlink()

        test_dir.rmdir()


    def test_ChainSequence(self):
        l1 = [1, 2, 3]
        l2 = [3, 4, 6]
        seq = documents.ChainSequence(l1, l2)
        seq[0] = 7
        seq[5], seq[3] = seq[3], seq[5]
        assert seq[5] == l2[2]
        as#TODO: foo'


]
ssert seT#TODO: foo'


<.#TODO: foo'


ODO: 2']
O#T#TODO: foo'




OTODO: 2']


TODO: {item<.*$>}')



o#TOTODO: 2']





DO:
O:
OTODO: {TODO: {item<#TODO: 2']









TODO: {item<#TODO: 2']



: thing
#TODO: 2']


#TODO: foo'



#TODO: foo'


#TODO: foo#TOD#TODO: foo#TODO: f#TODO: 7'TODO:





#TODO: foo#TODO: f#TODO: 7'TODO:



#TODO: f#TODO: 7'TODO:

#TODO: 7'TODO:
#TODO: 7'TTODO: thin#TODO: RTODO: {item<.TODO: thing




TODO: thin#TODO: RTODO: {item<.TODO: thing



#TODO: RTODO: {item<.TODO: thing


TODO: {item<.TODO: thing

TODO: thing
#TODO: {i#TODO:
#TODO: Read
TODO: {item<TODO: thing

TODO: thing
TODO: {item<.*>}$')
TODO: thing
#TODO: Read
