#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Test script for deko module

Latest version can be found at https://github.com/letuananh/chirptext

@author: Le Tuan Anh <tuananh.ke@gmail.com>
@license: MIT
'''

# Copyright (c) 2017, Le Tuan Anh <tuananh.ke@gmail.com>
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

########################################################################

import os
import unittest
import logging

from chirptext.deko import wakati, tokenize, analyse, txt2mecab, tokenize_sent, DekoText

# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
txt = '雨が降る。'
txt2 = '猫が好きです。\n犬も好きです。'
txt3 = '猫が好きです。\n犬も好きです。\n鳥は'


def getLogger():
    return logging.getLogger(__name__)


# -------------------------------------------------------------------------------
# Data Structures
# -------------------------------------------------------------------------------

class TestMainApp(unittest.TestCase):

    def test_mecab(self):
        tokens = txt2mecab(txt)
        self.assertTrue(tokens[-1].is_eos)

    def test_wakati(self):
        tks = wakati(txt)
        self.assertEqual(tks, '雨 が 降る 。 \n')

    def test_deko(self):
        tokenized = tokenize(txt)
        self.assertEqual(tokenized, ['雨', 'が', '降る', '。'])

    def test_analyse2(self):
        sents = DekoText.parse(txt)
        self.assertEqual(len(sents), 1)
        self.assertEqual(len(sents[0]), 5)
        self.assertEqual(str(sents[0]), '雨 が 降る 。')
        # 2 sentences
        sents = DekoText.parse(txt2)
        self.assertEqual(len(sents), 2)
        self.assertEqual(len(sents[0]), 6)
        self.assertEqual(len(sents[1]), 6)
        self.assertEqual(sents[0].words, ['猫', 'が', '好き', 'です', '。'])
        self.assertEqual(str(sents[1]), '犬 も 好き です 。')
        # 2 sentences
        sents = DekoText.parse(txt2, splitlines=False)
        self.assertEqual(len(sents), 2)
        self.assertEqual(len(sents[0]), 5)
        self.assertEqual(len(sents[1]), 5)
        self.assertEqual(str(sents[0]), '猫 が 好き です 。')
        self.assertEqual(str(sents[1]), '犬 も 好き です 。')

    def test_analyse(self):
        sents = analyse(txt2, format='txt')
        self.assertEqual(sents, '猫 が 好き です 。\n犬 も 好き です 。')
        # test sent tokenizing using MeCab
        tokens = txt2mecab(txt2)
        sents = tokenize_sent(tokens)
        # using analyse function
        sents = analyse(txt2, splitlines=False, format='txt').split('\n')
        self.assertEqual(sents, ['猫 が 好き です 。', '犬 も 好き です 。'])
        # to html
        h = analyse(txt, format='html')
        self.assertEqual(h, '<ruby><rb>雨</rb><rt>あめ</rt></ruby> が <ruby><rb>降る</rb><rt>ふる</rt></ruby>。 ')
        # to csv
        c = analyse(txt, format='csv')
        e = '''雨	名詞	一般	*	*	*	*	雨	アメ	アメ
が	助詞	格助詞	一般	*	*	*	が	ガ	ガ
降る	動詞	自立	*	*	五段・ラ行	基本形	降る	フル	フル
。	記号	句点	*	*	*	*	。	。	。
EOS									
'''
        self.assertEqual(c, e)

    def test_pos(self):
        sent = txt2mecab(txt)
        self.assertTrue(sent[-1].is_eos)
        poses = [tk.pos3() for tk in sent if not tk.is_eos]
        self.assertEqual(poses, ['名詞-一般', '助詞-格助詞-一般', '動詞-自立', '記号-句点'])
        for tk in sent:
            getLogger().debug(tk.pos3())

    def test_not_split(self):
        doc = DekoText.parse(txt3, splitlines=False)
        docx = DekoText.parse(txt3, splitlines=True)
        self.assertEqual([x.surface for x in doc], [x.surface for x in docx])
        getLogger().debug(doc)


# -------------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
