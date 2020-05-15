import re
import time
import string
import random
import textobjects
from textobjects import documents, matchlines
from textobjects.textobject import textobjecttypes
from pathlib import Path
from unittest import main, TestCase

ToDo = textobjects.create('ToDo', '#TODO: {item<.*>}$')
todos_file = Path('todo.txt')

class TestDocuments(TestCase):
    def setUp(self):
        todos_file.touch()

    def test_Page(self):
        with textobjects.page(todos_file, ToDo) as todos:
            todos.clear()
            todos.extend(['#TODO: foobar', '#TODO: bar'])
            assert len(todos) == 2

    def test_Document(TestCase):
        with textobjects.page(todos_file, ToDo) as p1:
            p1 += ['#TODO: 1', '#TODO: 2']
            document = documents.Document(p1, *[documents.Page('#TODO: foo', ToDo) for i in range(0, 9)])
            assert len(document) == 11
            assert p1 in document
            assert '#TODO: foo' in document

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
        assert seq[3] == l2[0]
        assert seq[0] == 7 == l1[0]

    def tearDown(self):
        todos_file.unlink()


if __name__ == '__main__':
    main()
