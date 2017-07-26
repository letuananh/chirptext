#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Script for testing leutile
Latest version can be found at https://github.com/letuananh/pydemo

References:
    Python documentation:
        https://docs.python.org/
    Python unittest
        https://docs.python.org/3/library/unittest.html
    --
    argparse module:
        https://docs.python.org/3/howto/argparse.html
    PEP 257 - Python Docstring Conventions:
        https://www.python.org/dev/peps/pep-0257/

@author: Le Tuan Anh <tuananh.ke@gmail.com>
'''

# Copyright (c) 2015, Le Tuan Anh <tuananh.ke@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

__author__ = "Le Tuan Anh <tuananh.ke@gmail.com>"
__copyright__ = "Copyright 2015, pydemo"
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

########################################################################

import os
import unittest
from chirptext import header
from chirptext.texttaglib import TagInfo, TaggedSentence, TaggedDoc
from chirptext.deko import txt2mecab

########################################################################

TEST_DIR = os.path.dirname(__file__)
TEST_DATA = os.path.join(TEST_DIR, 'data')


class TestMain(unittest.TestCase):

    def test_taginfo(self):
        print("Test tag info")
        t = TagInfo(1, 4, 'dog', TagInfo.ISF)
        self.assertEqual(t.cfrom, 1)
        self.assertEqual(t.cto, 4)
        self.assertEqual(t.label, 'dog')
        self.assertEqual(t.source, TagInfo.ISF)

        # Source = DEFAULT now
        t2 = TagInfo(0, 5, 'bark')
        self.assertEqual(t2.cfrom, 0)
        self.assertEqual(t2.cto, 5)
        self.assertEqual(t2.label, 'bark')
        self.assertEqual(t2.source, TagInfo.DEFAULT)

    def test_tagged_sentences(self):
        sent = TaggedSentence('猫が好きです 。')
        mecab_sent = txt2mecab(sent.text)
        # import tags
        sent.import_tokens(mecab_sent.words)
        for mtoken, token in zip(mecab_sent, sent.tokens):
            if mtoken.reading_hira() != token.label:
                token.tag(mtoken.reading_hira())
        self.assertEqual(mecab_sent.words, [x.label for x in sent.tokens])
        self.assertEqual(sent.tokens[0].tags[0].label, 'ねこ')
        self.assertEqual(sent.tokens[2].tags[0].label, 'すき')
        self.assertFalse(sent.tokens[1].tags)
        self.assertFalse(sent.tokens[3].tags)
        self.assertFalse(sent.tokens[4].tags)

    def test_tagging_erg_sent(self):
        txt = '''In this way I am no doubt indirectly responsible for Dr. Grimesby Roylott's death, and I cannot say that it is likely to weigh very heavily upon my conscience."'''
        words = ['in', 'this', 'way', 'i', 'am', 'no', 'doubt', 'indirectly', 'responsible', 'for', 'dr.', 'Grimesby', 'Roylott', "'s", 'death', ',', 'and', 'i', 'can', 'not', 'say', 'that', 'it', 'is', 'likely', 'to', 'weigh', 'very', 'heavily', 'upon', 'my', 'conscience', '.', '"']
        s = TaggedSentence(txt)
        s.import_tokens(words)
        self.assertEqual(words, [x.label for x in s.tokens])

    def test_tagged_doc(self):
        doc = TaggedDoc(TEST_DATA, 'test')
        doc.read()
        ts_count = [(len(s), len(s.concepts)) for s in doc]
        self.assertEqual(len(doc), 3)  # 3 sents
        self.assertEqual(ts_count, [(29, 15), (28, 13), (34, 23)])
        # for sent in doc:
        #     header(sent, 'h0')
        #     for tk in sent:
        #         print(tk)
        #     header('Concepts')
        #     for c in sent.concepts:
        #         print(c)
        #     print("")

    def test_cwl(self):
        doc = TaggedDoc(TEST_DATA, 'test').read()
        sent = doc[0]
        # ensure that words and concepts are linked properly
        w = doc[0][-4]
        c = sent.wclinks[w][0]
        tag = w.tag_map['pos'][0]
        self.assertEqual(tag.label, 'WP')
        self.assertEqual(c.words[0].tag_map['pos'][0].label, 'WP')
        tag.label = 'x'
        self.assertEqual(c.words[0].tag_map['pos'][0].label, 'x')

    def test_multiple_tags(self):
        doc = TaggedDoc(TEST_DATA, 'test').read()
        mw_ms = [(len(s.mwe), len(s.msw)) for s in doc]
        print(mw_ms)
        self.assertEqual(mw_ms, [(2, 2), (0, 0), (3, 2)])


########################################################################

def main():
    unittest.main()


if __name__ == "__main__":
    main()
