#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Test script for deko module

Latest version can be found at https://github.com/letuananh/chirptext

:copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
:license: MIT, see LICENSE for more details.
'''

import os
import unittest
import logging

from chirptext import TextReport
from chirptext import deko
from chirptext.deko import KATAKANA, simple_kata2hira
from chirptext.deko import wakati, tokenize, tokenize_sent, analyse, parse
from chirptext.deko import MeCabSent, DekoText
# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
txt = '雨が降る。'
txt2 = '猫が好きです。\n犬も好きです。'
txt3 = '猫が好きです。\n犬も好きです。\n鳥は'
txt4 = '猫が好きです。犬も好きです。鳥は'


def getLogger():
    return logging.getLogger(__name__)


# -------------------------------------------------------------------------------
# Test cases
# -------------------------------------------------------------------------------

class TestTool(unittest.TestCase):

    ALL_MAPPING = '''ぁァ|あア|ぃィ|いイ|ぅゥ|うウ|ぇェ|えエ|ぉォ|おオ|かカ|がガ|きキ|ぎギ|くク|ぐグ|けケ|げゲ|こコ|ごゴ|さサ|ざザ|しシ|じジ|すス|ずズ|せセ|ぜゼ|そソ|ぞゾ|たタ|だダ|ちチ|ぢヂ|っッ|つツ|づヅ|てテ|でデ|とト|どド|なナ|にニ|ぬヌ|ねネ|のノ|はハ|ばバ|ぱパ|ひヒ|びビ|ぴピ|ふフ|ぶブ|ぷプ|へヘ|べベ|ぺペ|ほホ|ぼボ|ぽポ|まマ|みミ|むム|めメ|もモ|ゃャ|やヤ|ゅュ|ゆユ|ょョ|よヨ|らラ|りリ|るル|れレ|ろロ|ゎヮ|わワ|ゐヰ|ゑヱ|をヲ|んン|ゔヴ|ゕヵ|ゖヶ|'''

    def test_kata2hira(self):
        rp = TextReport.string()
        for k in KATAKANA[1:87]:
            h = simple_kata2hira(k)
            rp.write(h, k, '|', separator='')
        expected = TestTool.ALL_MAPPING
        self.assertEqual(rp.content(), expected)

    def test_check_kana(self):
        self.assertTrue(deko.is_kana(''))
        self.assertRaises(ValueError, lambda: deko.is_kana(None))
        self.assertTrue(deko.is_kana('ひらがな'))
        self.assertTrue(deko.is_kana('カタカナ'))
        self.assertTrue(deko.is_kana(TestTool.ALL_MAPPING.replace('|', '')))
        # false
        self.assertFalse(deko.is_kana(TestTool.ALL_MAPPING))  # with pipe
        self.assertFalse(deko.is_kana('巡り会う'))  # with kanji
        self.assertFalse(deko.is_kana('すき です'))  # with a space


class TestDeko(unittest.TestCase):

    def test_mecab(self):
        print("Testing mecab")
        tokens = parse(txt)
        self.assertTrue(tokens[-1].is_eos)

    def test_mecab_bin_loc(self):
        mbin_original = deko.get_mecab_bin()
        if mbin_original:
            self.assertTrue(mbin_original == 'mecab' or mbin_original.endswith('mecab.exe'))
        with self.assertLogs('chirptext.dekomecab', level='WARNING') as log:
            mecab_custom_loc = 'C:\\mecab\\mecab-console.exe'
            deko.set_mecab_bin(mecab_custom_loc)
            self.assertEqual(deko.get_mecab_bin(), mecab_custom_loc)
            if not os.path.isfile(mecab_custom_loc):
                self.assertEqual(log.output, ['WARNING:chirptext.dekomecab:Provided mecab binary location does not exist C:\\mecab\\mecab-console.exe'])
            # set it back
        with self.assertLogs('chirptext.dekomecab', level='WARNING') as log:
            deko.set_mecab_bin(mbin_original)
            if not os.path.isfile(mbin_original):
                self.assertEqual(log.output, ['WARNING:chirptext.dekomecab:Provided mecab binary location does not exist ' + mbin_original])

    def test_dekomecab(self):
        # try parsing text using mecab binary
        self.assertRaises(FileNotFoundError, lambda: parse(txt, mecab_loc='/usr/bin/path/to/mecab-binary-app'))
        self.assertRaises(FileNotFoundError, lambda: analyse(txt, mecab_loc='/usr/bin/path/to/mecab-binary-app'))
        self.assertRaises(FileNotFoundError, lambda: DekoText.parse(txt, mecab_loc='/usr/bin/path/to/mecab-binary-app'))
        self.assertRaises(FileNotFoundError, lambda: MeCabSent.parse(txt, mecab_loc='/usr/bin/path/to/mecab-binary-app'))

    def test_mecab_lines(self):
        out = parse(txt2)
        self.assertGreaterEqual(len(out), 11)

    def test_wakati(self):
        tks = wakati(txt).splitlines()[0]
        self.assertEqual(tks, '雨 が 降る 。 ')

    def test_deko(self):
        tokenized = tokenize(txt)
        self.assertEqual(tokenized, ['雨', 'が', '降る', '。'])

    def test_tokenize_sents(self):
        tokens = parse(txt2)
        sents = tokenize_sent(tokens, txt2)
        texts = [x.text for x in sents]
        self.assertEqual(texts, ['猫が好きです。', '犬も好きです。'])

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
        getLogger().debug("Tokenized: ", parse(txt2))
        sents = DekoText.parse(txt2, splitlines=False)
        getLogger().debug("last test: {} - {} sents".format(sents, len(sents)))
        self.assertEqual(len(sents), 2)
        self.assertEqual(len(sents[0]), 5)
        self.assertEqual(len(sents[1]), 5)
        self.assertEqual(str(sents[0]), '猫 が 好き です 。')
        self.assertEqual(str(sents[1]), '犬 も 好き です 。')

    def test_analyse(self):
        sents = analyse(txt2, format='txt')
        self.assertEqual(sents, '猫 が 好き です 。\n犬 も 好き です 。')
        # test sent tokenizing using MeCab
        tokens = parse(txt2)
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
        sent = parse(txt)
        self.assertTrue(sent[-1].is_eos)
        poses = [tk.pos3() for tk in sent if not tk.is_eos]
        self.assertEqual(poses, ['名詞-一般', '助詞-格助詞-一般', '動詞-自立', '記号-句点'])
        for tk in sent:
            getLogger().debug(tk.pos3())

    def test_deko_ttl(self):
        sent = parse(txt).to_ttl()
        getLogger().debug("Sent: {}".format(sent))
        for tk in sent:
            getLogger().debug("{} - {}".format(tk, tk.pos))
        sj = sent.to_json()
        getLogger().debug(sj)
        expected = {'text': '雨が降る。', 'tokens': [{'cfrom': 0, 'cto': 1, 'text': '雨', 'lemma': '雨', 'pos': '名詞-一般', 'tags': [{'label': 'あめ', 'type': 'reading', 'source': 'mecab'}]}, {'cfrom': 1, 'cto': 2, 'text': 'が', 'lemma': 'が', 'pos': '助詞-格助詞-一般', 'tags': [{'label': 'が', 'type': 'reading', 'source': 'mecab'}]}, {'cfrom': 2, 'cto': 4, 'text': '降る', 'lemma': '降る', 'pos': '動詞-自立', 'tags': [{'label': 'ふる', 'type': 'reading', 'source': 'mecab'}]}, {'cfrom': 4, 'cto': 5, 'text': '。', 'lemma': '。', 'pos': '記号-句点', 'tags': [{'label': '。', 'type': 'reading', 'source': 'mecab'}]}]}
        self.assertEqual(sj, expected)
        # test doc to ttl
        doc = DekoText.parse(txt3, splitlines=True)
        ttl_doc = doc.to_ttl()
        self.assertEqual(len(ttl_doc), 3)
        for ds, ts in zip(doc, ttl_doc):
            self.assertEqual(ds.text, ts.text)
            for dtk, ttk in zip(ds, ts):
                self.assertEqual(dtk.surface, ttk.text)
                self.assertEqual(dtk.pos3(), ttk.pos)

    def test_analyse_multiple_sents(self):
        msent = parse(txt4)
        getLogger().debug(msent.tokens)
        sent = msent.to_ttl()
        expected_tokens = ['猫', 'が', '好き', 'です', '。', '犬', 'も', '好き', 'です', '。', '鳥', 'は']
        tokens = [tk.text for tk in sent.tokens]
        self.assertEqual(tokens, expected_tokens)
        # check reading
        readings = [tk.get_tag('reading').label for tk in sent.tokens]
        expected_readings = ['ねこ', 'が', 'すき', 'です', '。', 'いぬ', 'も', 'すき', 'です', '。', 'とり', 'は']
        self.assertEqual(readings, expected_readings)
        # try tokenizing sentences
        sents = tokenize_sent(msent.tokens, txt4)
        expected = [['猫が好きです。', ['猫', 'が', '好き', 'です', '。']], ['犬も好きです。', ['犬', 'も', '好き', 'です', '。']], ['鳥は', ['鳥', 'は']]]
        actual = [[sent.surface, sent.words] for sent in sents]
        self.assertEqual(actual, expected)

    def test_not_split(self):
        doc = DekoText.parse(txt3, splitlines=False)
        docx = DekoText.parse(txt3, splitlines=True)
        doc_words = [x.surface for x in doc]
        docx_words = [x.surface for x in docx]
        getLogger().debug("splitlines: {} | surface={}".format(docx, docx_words))
        getLogger().debug("not splitlines: {} | surface={}".format(doc, doc_words))
        self.assertEqual(doc_words, docx_words)
        getLogger().debug(doc)

    def test_func_alias(self):
        sent = deko.parse(txt)
        self.assertEqual(sent.words, ['雨', 'が', '降る', '。'])
        doc = deko.parse_doc(txt3, splitlines=False)
        self.assertEqual(len(doc), 3)


# -------------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
