#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for deko module
"""

# This code is a part of chirptext library: https://github.com/letuananh/chirptext
# :copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import logging
import os
import unittest

from chirptext import TextReport
from chirptext import deko
from chirptext.deko import get_mecab_bin, set_mecab_bin
from chirptext.deko import dekoigo
from chirptext.deko import tokenize, analyse, parse, parse_doc
from chirptext.deko.util import KATAKANA, simple_kata2hira, is_kana
from chirptext.deko.mecab import version, wakati

# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
txt = '雨が降る。'
txt2 = '猫が好きです。\n犬も好きです。'
txt3 = '猫が好きです。\n犬も好きです。\n鳥は'
txt4 = '猫が好きです。犬も好きです。鳥は'

_MECAB_VERSION = None
try:
    _MECAB_VERSION = version()
except Exception:
    print("WARNING: mecab binary is not available. All dekomecab tests will be ignored.")

if not dekoigo.igo_available():
    print("WARNING: igo-python is not available. All igo test will be ignored.")


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
        self.assertTrue(is_kana(''))
        self.assertRaises(ValueError, lambda: is_kana(None))
        self.assertTrue(is_kana('ひらがな'))
        self.assertTrue(is_kana('カタカナ'))
        self.assertTrue(is_kana(TestTool.ALL_MAPPING.replace('|', '')))
        # false
        self.assertFalse(is_kana(TestTool.ALL_MAPPING))  # with pipe
        self.assertFalse(is_kana('巡り会う'))  # with kanji
        self.assertFalse(is_kana('すき です'))  # with a space


@unittest.skipIf(not _MECAB_VERSION,
                 "Mecab binary is not available, all mecab related tests will be ignored")
class TestDekoMecab(unittest.TestCase):

    def test_tokenize_sents(self):
        lines = deko.mecab._internal_mecab_parse(txt2).splitlines()
        token_dicts = [deko.mecab._mecab_line_to_token_dicts(line) for line in lines]
        sents = deko.mecab._tokenize_token_dicts(token_dicts, txt2)
        texts = [x.text for x in sents]
        self.assertEqual(texts, ['猫が好きです。', '犬も好きです。'])


@unittest.skipIf(not _MECAB_VERSION,
                 "Mecab binary is not available, all mecab related tests will be ignored")
class TestDeko(unittest.TestCase):

    def test_mecab_version(self):
        v = version()
        print(f"Testing deko using mecab version: {v}")
        self.assertIn("mecab", v)

    def test_mecab_available(self):
        engines = {x[0] for x in deko.engines()}
        self.assertIn("mecab", engines)

    def test_mecab(self):
        sent = parse(txt)
        self.assertEqual(['雨', 'が', '降る', '。'], list(sent.tokens.values()))

    def test_mecab_bin_loc(self):
        mbin_original = get_mecab_bin()
        mbin_locs = ['mecab', 'mecab.exe', '/usr/local/bin/mecab', '/usr/bin/mecab']
        self.assertTrue(mbin_original)  # there must be a default mecab binary even when the binary is not available
        with self.assertLogs('chirptext.deko', level='WARNING') as log:
            mecab_custom_loc = 'C:\\mecab-na\\mecab-console.exe'
            set_mecab_bin(mecab_custom_loc)
            self.assertEqual(get_mecab_bin(), mecab_custom_loc)
            if not os.path.isfile(mecab_custom_loc):
                self.assertEqual(log.output, [
                    'WARNING:chirptext.deko.mecab:Provided mecab binary location does not exist (C:\\mecab-na\\mecab-console.exe)'])
        if not os.path.isfile(mbin_original):
            # this should shout a warning too
            with self.assertLogs('chirptext.deko', level='WARNING') as log:
                set_mecab_bin(mbin_original)
                getLogger().debug(f"Original mbin: {mbin_original}")
                getLogger().debug(f"log.output: {log}")
                getLogger().debug(f"{os.path.isfile(mbin_original)}")
                self.assertEqual(log.output, [
                    f'WARNING:chirptext.deko.mecab:Provided mecab binary location does not exist ({mbin_original})'])
        else:
            # set it back after tested
            set_mecab_bin(mbin_original)

    def test_dekomecab(self):
        # try parsing text using mecab binary
        self.assertRaises(FileNotFoundError, lambda: parse(txt, mecab_loc='/usr/bin/path/to/mecab-binary-app'))
        self.assertRaises(FileNotFoundError, lambda: analyse(txt, mecab_loc='/usr/bin/path/to/mecab-binary-app'))
        self.assertRaises(FileNotFoundError, lambda: deko.parse(txt, mecab_loc='/usr/bin/path/to/mecab-binary-app'))
        self.assertRaises(FileNotFoundError, lambda: deko.parse_doc(txt, mecab_loc='/usr/bin/path/to/mecab-binary-app'))

    def test_mecab_lines(self):
        out = parse(txt2)
        self.assertGreaterEqual(len(out), 10)  # EOS is removed automatically

    def test_wakati(self):
        tks = wakati(txt).splitlines()[0]
        self.assertEqual(tks, '雨 が 降る 。 ')

    def test_deko(self):
        tokenized = tokenize(txt, use_wakati=False)
        self.assertEqual(tokenized, ['雨', 'が', '降る', '。'])

    def test_analyse2(self):
        doc = deko.parse_doc(txt)
        self.assertEqual(len(doc), 1)
        self.assertEqual(len(doc[0]), 4)
        self.assertEqual('雨が降る。', str(doc[0]))
        # 2 sentences
        results = [
            deko.parse_doc(txt2),
            deko.parse_doc(txt2, splitlines=False)
        ]
        for doc in results:
            self.assertEqual(2, len(doc))
            self.assertEqual(5, len(doc[0]))
            self.assertEqual(5, len(doc[1]))
            self.assertEqual('猫が好きです。', str(doc[0]))
            self.assertEqual('犬も好きです。', str(doc[1]))
            self.assertEqual(['猫', 'が', '好き', 'です', '。'], list(doc[0].tokens.values()))
            self.assertEqual(['犬', 'も', '好き', 'です', '。'], list(doc[1].tokens.values()))

    def test_analyse(self):
        sents = analyse(txt2, format='txt')
        self.assertEqual(sents, '猫 が 好き です 。\n犬 も 好き です 。')
        # using analyse function
        sents = analyse(txt2, splitlines=False, format='txt').split('\n')
        self.assertEqual(sents, ['猫 が 好き です 。', '犬 も 好き です 。'])
        # to html
        h = analyse(txt, format='html')
        self.assertEqual(h, '<ruby><rb>雨</rb><rt>あめ</rt></ruby> が <ruby><rb>降る</rb><rt>ふる</rt></ruby>。')
        # to csv
        c = analyse(txt, format='csv')
        e = '''雨	名詞	一般	*	*	*	*	雨	アメ	アメ
が	助詞	格助詞	一般	*	*	*	が	ガ	ガ
降る	動詞	自立	*	*	五段・ラ行	基本形	降る	フル	フル
。	記号	句点	*	*	*	*	。	。	。'''
        self.assertEqual(e, c.strip())

    def test_pos(self):
        sent = parse(txt)
        poses = [tk.pos3 for tk in sent]
        self.assertEqual(poses, ['名詞-一般', '助詞-格助詞-一般', '動詞-自立', '記号-句点'])

    def test_deko_ttl(self):
        sent = parse(txt)
        sj = sent.to_dict()
        expected = {'text': '雨が降る。',
                    'tokens': [{'cfrom': 0, 'cto': 1, 'lemma': '雨', 'pos': '名詞',
                                'tags': [{'type': 'sc1', 'value': '一般'},
                                         {'type': 'pos3', 'value': '名詞-一般'},
                                         {'type': 'reading_hira', 'value': 'あめ'}],
                                'text': '雨'},
                               {'cfrom': 1, 'cto': 2, 'lemma': 'が', 'pos': '助詞',
                                'tags': [{'type': 'sc1', 'value': '格助詞'},
                                         {'type': 'sc2', 'value': '一般'},
                                         {'type': 'pos3', 'value': '助詞-格助詞-一般'},
                                         {'type': 'reading_hira', 'value': 'が'}],
                                'text': 'が'},
                               {'cfrom': 2, 'cto': 4, 'lemma': '降る', 'pos': '動詞',
                                'tags': [{'type': 'sc1', 'value': '自立'},
                                         {'type': 'inf', 'value': '五段・ラ行'},
                                         {'type': 'conj', 'value': '基本形'},
                                         {'type': 'pos3', 'value': '動詞-自立'},
                                         {'type': 'reading_hira', 'value': 'ふる'}],
                                'text': '降る'},
                               {'cfrom': 4, 'cto': 5, 'lemma': '。', 'pos': '記号',
                                'tags': [{'type': 'sc1', 'value': '句点'},
                                         {'type': 'pos3', 'value': '記号-句点'},
                                         {'type': 'reading_hira', 'value': '。'}],
                                'text': '。'}]}
        self.assertEqual(sj, expected)
        # test doc to ttl
        ttl_doc = deko.parse_doc(txt3, splitlines=True)
        self.assertEqual(len(ttl_doc), 3)

        for sent, sent_text in zip(ttl_doc, txt3.splitlines()):
            tokens = deko.tokenize(sent_text, use_wakati=True)
            self.assertEqual(sent.text, sent_text)
            self.assertEqual(tokens, list(sent.tokens.values()))

    def test_analyse_multiple_sents(self):
        sent = parse(txt4)
        expected_tokens = ['猫', 'が', '好き', 'です', '。', '犬', 'も', '好き', 'です', '。', '鳥', 'は']
        tokens = list(sent.tokens.values())
        self.assertEqual(tokens, expected_tokens)
        # check reading
        readings = [tk.reading_hira for tk in sent]
        expected_readings = ['ねこ', 'が', 'すき', 'です', '。', 'いぬ', 'も', 'すき', 'です', '。', 'とり', 'は']
        self.assertEqual(readings, expected_readings)
        # try tokenizing sentences
        doc = deko.parse_doc(txt4, splitlines=False)
        expected = [['猫が好きです。', ['猫', 'が', '好き', 'です', '。']],
                    ['犬も好きです。', ['犬', 'も', '好き', 'です', '。']],
                    ['鳥は', ['鳥', 'は']]]
        actual = [[sent.text, list(sent.tokens.values())] for sent in doc]
        self.assertEqual(expected, actual)
        # try tokenize text to sentences
        sents = deko.tokenize_sent(txt4)
        expected = ['猫が好きです。', '犬も好きです。', '鳥は']
        self.assertEqual(expected, sents)

    def test_not_split(self):
        doc = deko.parse_doc(txt3, splitlines=False)
        docx = deko.parse_doc(txt3, splitlines=True)
        doc_words = [x.text for x in doc]
        docx_words = [x.text for x in docx]
        self.assertEqual(doc_words, docx_words)

    def test_func_alias(self):
        sent = parse(txt)
        self.assertEqual(sent.tokens.values(), ['雨', 'が', '降る', '。'])
        doc = parse_doc(txt3, splitlines=False)
        self.assertEqual(len(doc), 3)


@unittest.skipIf(not dekoigo.igo_available(),
                 "igo library is not available, all dekoigo tests will be ignored")
class TestDekoigo(unittest.TestCase):

    def test_igo_available(self):
        engines = {x[0] for x in deko.engines()}
        self.assertIn("igo", engines)

    def test_dekoigo_tokenizer(self):
        # tokenize words
        words = dekoigo.tokenize(txt)
        expected_words = ['雨', 'が', '降る', '。']
        self.assertEqual(expected_words, words)
        sents = dekoigo.tokenize_sent(txt4)
        expected = ['猫が好きです。', '犬も好きです。', '鳥は']
        self.assertEqual(expected, sents)

    def test_dekoigo_parse(self):
        self.assertTrue(dekoigo.igo_available())
        sent = dekoigo.parse(",があります。")
        expected = [',', 'が', 'あり', 'ます', '。']
        self.assertEqual(expected, sent.tokens.values())
        poses = ['名詞-サ変接続', '助詞-格助詞-一般', '動詞-自立', '助動詞', '記号-句点']
        self.assertEqual(poses, [t.pos3 for t in sent])
        # try parsing momo
        sent = dekoigo.parse("すもももももももものうち")
        features = [(t.text, t.pos3) for t in sent]
        expected = [('すもも', '名詞-一般'),
                    ('も', '助詞-係助詞'),
                    ('もも', '名詞-一般'),
                    ('も', '助詞-係助詞'),
                    ('もも', '名詞-一般'),
                    ('の', '助詞-連体化'),
                    ('うち', '名詞-非自立-副詞可能')]
        self.assertEqual(expected, features)

    def test_dekoigo_parse_doc(self):
        doc1 = dekoigo.parse_doc(txt3)
        poses = [[(t.surface(), t.pos3, t.reading_hira) for t in s] for s in doc1]
        expected = [[('猫', '名詞-一般', 'ねこ'),
                     ('が', '助詞-格助詞-一般', 'が'),
                     ('好き', '名詞-形容動詞語幹', 'すき'),
                     ('です', '助動詞', 'です'),
                     ('。', '記号-句点', '。')],
                    [('犬', '名詞-一般', 'いぬ'),
                     ('も', '助詞-係助詞', 'も'),
                     ('好き', '名詞-形容動詞語幹', 'すき'),
                     ('です', '助動詞', 'です'),
                     ('。', '記号-句点', '。')],
                    [('鳥', '名詞-一般', 'とり'), ('は', '助詞-係助詞', 'は')]]
        self.assertEqual(expected, poses)
        doc2 = dekoigo.parse_doc(txt3, splitlines=False)
        self.assertEqual([s.to_dict() for s in doc1], [s.to_dict() for s in doc2])


@unittest.skipIf(not deko.janome.janome_available(),
         "Janome library is not available, all janome related tests will be ignored")
class TestJanome(unittest.TestCase):

    def test_engine(self):
        engines = {x[0] for x in deko.engines()}
        self.assertIn("janome", engines)
    
    def test_janome_tokenizer(self):
        # tokenize words
        words = deko.janome.tokenize(txt)
        expected_words = ['雨', 'が', '降る', '。']
        self.assertEqual(expected_words, words)
        sents = deko.janome.tokenize_sent(txt4)
        expected = ['猫が好きです。', '犬も好きです。', '鳥は']
        self.assertEqual(expected, sents)

    def test_janome_parse(self):
        self.assertTrue(deko.janome.janome_available())
        sent = deko.janome.parse(",があります。")
        expected = [',', 'が', 'あり', 'ます', '。']
        self.assertEqual(expected, sent.tokens.values())
        poses = ['記号-読点', '助詞-格助詞-一般', '動詞-自立', '助動詞', '記号-句点']
        self.assertEqual(poses, [t.pos3 for t in sent])
        # try parsing momo
        sent = deko.janome.parse("すもももももももものうち")
        features = [(t.text, t.pos3) for t in sent]
        expected = [('すもも', '名詞-一般'),
                    ('も', '助詞-係助詞'),
                    ('もも', '名詞-一般'),
                    ('も', '助詞-係助詞'),
                    ('もも', '名詞-一般'),
                    ('の', '助詞-連体化'),
                    ('うち', '名詞-非自立-副詞可能')]
        self.assertEqual(expected, features)

    def test_janome_parse_doc(self):
        doc1 = deko.janome.parse_doc(txt3)
        poses = [[(t.surface(), t.pos3, t.reading_hira) for t in s] for s in doc1]
        expected = [[('猫', '名詞-一般', 'ねこ'),
                     ('が', '助詞-格助詞-一般', 'が'),
                     ('好き', '名詞-形容動詞語幹', 'すき'),
                     ('です', '助動詞', 'です'),
                     ('。', '記号-句点', '。')],
                    [('犬', '名詞-一般', 'いぬ'),
                     ('も', '助詞-係助詞', 'も'),
                     ('好き', '名詞-形容動詞語幹', 'すき'),
                     ('です', '助動詞', 'です'),
                     ('。', '記号-句点', '。')],
                    [('鳥', '名詞-一般', 'とり'), ('は', '助詞-係助詞', 'は')]]
        self.assertEqual(expected, poses)
        doc2 = deko.janome.parse_doc(txt3, splitlines=False)
        self.assertEqual([s.to_dict() for s in doc1], [s.to_dict() for s in doc2])



# -------------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
