#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Script for testing leutile

Latest version can be found at https://github.com/letuananh/chirptext

@author: Le Tuan Anh <tuananh.ke@gmail.com>
@license: MIT
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

########################################################################

import os
import unittest
import logging
from chirptext import TextReport
from chirptext import texttaglib as ttl
from chirptext.deko import txt2mecab

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

TEST_DIR = os.path.dirname(__file__)
TEST_DATA = os.path.join(TEST_DIR, 'data')

BARK_SID = '01047745-v'
GDOG_SID = '02103841-n'


def getLogger():
    return logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------------------

class TestBuildTags(unittest.TestCase):

    def test_create_sent(self):
        doc = ttl.Document('test', TEST_DATA)
        # add words
        sent = doc.new_sent('Some happy guard-dogs barked.', 1)
        sent.import_tokens('Some happy guard dogs barked .'.split())
        self.assertEqual(len(sent), 6)
        # sense tagging
        sent.new_concept('01148283-a', 'happy', tokens=[sent[1]])
        c = sent.new_concept('02084071-n', 'dog')
        sent.concept(c.ID).add_token(sent[3])
        sent.new_concept(BARK_SID, 'bark').add_token(sent[4])
        sent.new_concept(GDOG_SID, 'guard-dog').add_token(sent[2], sent[3])  # MWE example
        # verification
        tcmap = sent.tcmap()
        self.assertEqual(tcmap[sent[3]][0].clemma, 'dog')
        self.assertEqual(tcmap[sent[3]][1].clemma, 'guard-dog')
        self.assertEqual(tcmap[sent[3]][1].tag, GDOG_SID)
        self.assertEqual(tcmap[sent[4]][0].tag, BARK_SID)
        mwe = list(sent.mwe())
        self.assertTrue(mwe)
        self.assertEqual(mwe[0].tag, GDOG_SID)


class TestTagging(unittest.TestCase):

    def test_taginfo(self):
        print("Test tag info")
        t = ttl.Tag('dog', 1, 4, source=ttl.Tag.ISF)
        self.assertEqual(t.cfrom, 1)
        self.assertEqual(t.cto, 4)
        self.assertEqual(t.label, 'dog')
        self.assertEqual(t.source, ttl.Tag.ISF)

        # Source = DEFAULT now
        t2 = ttl.Tag('bark', 0, 5)
        self.assertEqual(t2.cfrom, 0)
        self.assertEqual(t2.cto, 5)
        self.assertEqual(t2.label, 'bark')
        self.assertEqual(t2.source, ttl.Tag.DEFAULT)

    def test_tag_token(self):
        token = ttl.Token("Words", 0, 4)
        token.new_tag("plural")
        token.new_tag("word-token")
        token.pos = 'n'
        token.lemma = 'word'
        token.comment = "an element of speech or writing"
        js_token = token.to_json()
        expected = {"tags": {"unsorted": ["plural", "word-token"]}, "cfrom": 0, "pos": "n", "cto": 4, "text": "Words", "lemma": "word", 'comment': 'an element of speech or writing'}
        self.assertEqual(js_token, expected)

    def test_comment(self):
        sent = ttl.Sentence("Dogs bark.")
        sent.import_tokens("Dogs bark .".split())
        sent[0].comment = "canine"
        sent.new_concept("02084071-n", "dog", tokens=(sent[0],))
        sent.concepts[0].comment = 'a member of the genus Canis (probably descended from the common wolf) that has been domesticated by man since prehistoric times'
        expected = {'text': 'Dogs bark.', 'tokens': [{'cto': 4, 'cfrom': 0, 'comment': 'canine', 'text': 'Dogs'}, {'cto': 9, 'cfrom': 5, 'text': 'bark'}, {'cto': 10, 'cfrom': 9, 'text': '.'}], 'concepts': [{'tag': '02084071-n', 'clemma': 'dog', 'comment': 'a member of the genus Canis (probably descended from the common wolf) that has been domesticated by man since prehistoric times', 'tokens': [0]}]}
        print(sent.to_json())
        print(expected)
        self.assertEqual(expected, sent.to_json())
        self.assertFalse(sent.tags)
        sent.new_tag(GDOG_SID, 0, 4, tagtype='wn30')
        sent.new_tag(BARK_SID, 5, 9, tagtype='wn30')
        for t in sent.tags:
            getLogger().debug("{}: label={} | type = {}".format(t, t.label, t.tagtype))

    def test_tagged_sentences(self):
        sent = ttl.Sentence('猫が好きです 。')
        mecab_sent = txt2mecab(sent.text)
        # import tags
        sent.import_tokens(mecab_sent.words)
        for mtoken, token in zip(mecab_sent, sent.tokens):
            if mtoken.reading_hira() != token.text:
                if token.text in ('猫', '好き'):
                    token.new_tag(mtoken.reading_hira(), tagtype='reading')
                token.lemma = mtoken.reading_hira()
                token.pos = mtoken.pos3()
        self.assertEqual(mecab_sent.words, [x.text for x in sent.tokens])
        self.assertEqual(sent.tokens[0][0].label, 'ねこ')
        self.assertEqual(sent.tokens[0].lemma, 'ねこ')
        self.assertEqual(sent.tokens[2][0].label, 'すき')
        self.assertFalse(sent.tokens[3].lemma, '')  # if there is no lemma label => return ''
        self.assertEqual(sent.tokens[2].surface(), '好き')
        self.assertFalse(len(sent.tokens[1]))
        self.assertFalse(len(sent.tokens[3]))
        self.assertFalse(len(sent.tokens[4]))
        return sent

    def test_tagged_sent_to_json(self):
        sent = ttl.Sentence("女の子は猫が好きです。")
        sent.import_tokens("女 の 子 は 猫 が 好き です 。".split())
        sent[0].lemma = "おんな"
        sent[2].lemma = "こ"
        sent[4].lemma = "ねこ"
        sent[4].comment = "Say neh-koh"
        sent[4].pos = "名詞-一般"
        sent[6].lemma = "すき"
        sent[6].pos = "名詞-形容動詞語幹"
        sent.new_concept("10084295-n", "女の子", (sent[0], sent[1], sent[2]))
        sent.concepts[0].comment = "若々しい女の人"
        sent.new_concept("02121620-n", clemma="猫").add_token(sent[4])
        sent.new_concept("01292683-a", clemma="好き").add_token(sent[6])
        expected = {'tokens': [{'cfrom': 0, 'cto': 1, 'lemma': 'おんな', 'text': '女'},
                               {'cfrom': 1, 'cto': 2, 'text': 'の'},
                               {'cfrom': 2, 'cto': 3, 'lemma': 'こ', 'text': '子'},
                               {'cfrom': 3, 'cto': 4, 'text': 'は'},
                               {'pos': '名詞-一般', 'cfrom': 4, 'cto': 5, 'lemma': 'ねこ', 'text': '猫', 'comment': 'Say neh-koh'},
                               {'cfrom': 5, 'cto': 6, 'text': 'が'},
                               {'pos': '名詞-形容動詞語幹', 'cfrom': 6, 'cto': 8, 'lemma': 'すき', 'text': '好き'},
                               {'cfrom': 8, 'cto': 10, 'text': 'です'},
                               {'cfrom': 10, 'cto': 11, 'text': '。'}],
                    'text': '女の子は猫が好きです。',
                    'concepts': [{'tag': '10084295-n', 'tokens': [0, 1, 2], 'clemma': '女の子', 'comment': '若々しい女の人'},
                                 {'tag': '02121620-n', 'tokens': [4], 'clemma': '猫'},
                                 {'tag': '01292683-a', 'tokens': [6], 'clemma': '好き'}]}
        actual = sent.to_json()
        self.assertEqual(expected['text'], actual['text'])
        self.assertEqual(expected['concepts'], actual['concepts'])
        self.assertEqual(expected['tokens'], actual['tokens'])
        self.assertEqual(expected, actual)
        print(actual)

    def test_json_tagged_sent(self):
        raw = {'text': '女の子は猫が好きです。', 'tokens': [{'cfrom': 0, 'cto': 1, 'text': '女', 'lemma': 'おんな'}, {'cfrom': 1, 'cto': 2, 'text': 'の'}, {'cfrom': 2, 'cto': 3, 'text': '子', 'lemma': 'こ'}, {'cfrom': 3, 'cto': 4, 'text': 'は'}, {'cfrom': 4, 'cto': 5, 'text': '猫', 'lemma': 'ねこ', 'pos': '名詞-一般', 'comment': 'Say neh-koh'}, {'cfrom': 5, 'cto': 6, 'text': 'が'}, {'cfrom': 6, 'cto': 8, 'text': '好き', 'lemma': 'すき', 'pos': '名詞-形容動詞語幹'}, {'cfrom': 8, 'cto': 10, 'text': 'です'}, {'cfrom': 10, 'cto': 11, 'text': '。'}], 'concepts': [{'clemma': '女の子', 'tag': '10084295-n', 'tokens': [0, 1, 2], 'comment': '若々しい女の人', 'flag': 'G'}, {'clemma': '猫', 'tag': '02121620-n', 'tokens': [4]}, {'clemma': '好き', 'tag': '01292683-a', 'tokens': [6]}]}
        # json => TaggedSentence => json
        sent = ttl.Sentence.from_json(raw)
        sent_json = sent.to_json()
        self.assertEqual(raw['text'], sent_json['text'])
        self.assertEqual(raw['concepts'], sent_json['concepts'])
        self.assertEqual(raw['tokens'], sent_json['tokens'])
        self.assertEqual(raw, sent_json)
        self.assertEqual(sent_json['concepts'][0]['flag'], 'G')

    def test_tagging_erg_sent(self):
        txt = '''In this way I am no doubt indirectly responsible for Dr. Grimesby Roylott's death, and I cannot say that it is likely to weigh very heavily upon my conscience."'''
        words = ['in', 'this', 'way', 'i', 'am', 'no', 'doubt', 'indirectly', 'responsible', 'for', 'dr.', 'Grimesby', 'Roylott', "'s", 'death', ',', 'and', 'i', 'can', 'not', 'say', 'that', 'it', 'is', 'likely', 'to', 'weigh', 'very', 'heavily', 'upon', 'my', 'conscience', '.', '"']
        s = ttl.Sentence(txt)
        s.import_tokens(words)
        self.assertEqual(words, [x.text for x in s.tokens])

    def test_tagged_doc(self):
        doc = ttl.Document('test', TEST_DATA)
        doc.read()
        ts_count = [(len(s), len(s.concepts)) for s in doc]
        self.assertEqual(len(doc), 3)  # 3 sents
        self.assertEqual(ts_count, [(29, 15), (28, 13), (34, 23)])

    def test_cwl(self):
        doc = ttl.Document('test', TEST_DATA).read()
        sent = doc[0]
        # ensure that words and concepts are linked properly
        w = doc[0][-4]
        tcmap = sent.tcmap()
        c = tcmap[w][0]
        self.assertEqual(w.pos, 'WP')
        self.assertEqual(c.tokens[0].pos, 'WP')
        # test sentence level tagging
        self.assertTrue([str(t) for t in sent.tags])

    def test_multiple_tags(self):
        doc = ttl.Document('test', TEST_DATA).read()
        mw_ms = [(len(list(s.mwe())), len(list(s.msw()))) for s in doc]
        self.assertEqual(mw_ms, [(2, 2), (0, 0), (3, 2)])

    def test_recover_surface_string(self):
        s = ttl.Sentence('''a religious sect founded in the United States in 1966; based on Vedic scriptures; groups engage in joyful chanting of `Hare Krishna' and other mantras based on the name of the Hindu god Krishna; devotees usually wear saffron robes and practice vegetarianism and celibacy''')
        tokens = ['a', 'religious', 'sect', 'founded', 'in', 'the', 'United', 'States', 'in', '1966', ';', 'based', 'on', 'Vedic', 'scriptures', ';', 'groups', 'engage', 'in', 'joyful', 'chanting', 'of', 'Hare', 'Krishna', 'and', 'other', 'mantras', 'based', 'on', 'the', 'name', 'of', 'the', 'Hindu', 'god', 'Krishna', ';', 'devotees', 'usually', 'wear', 'saffron', 'robes', 'and', 'practice', 'vegetarianism', 'and', 'celibacy']
        s.import_tokens(tokens)
        cfrom = min(x.cfrom for x in s.tokens)
        cto = max(x.cto for x in s.tokens)
        self.assertEqual(s.text, s.text[cfrom:cto])

    def test_export_to_streams(self):
        concepts = TextReport.string()
        links = TextReport.string()
        sents = TextReport.string()
        tags = TextReport.string()
        words = TextReport.string()
        doc = ttl.Document('manual', TEST_DATA)
        # create sents in doc
        raws = ("三毛猫がすきです。", "雨が降る。", "女の子はケーキを食べる。")
        for sid, r in enumerate(raws):
            msent = txt2mecab(r)
            tsent = doc.new_sent(msent.surface, sid)
            tsent.import_tokens(msent.words)
            # pos tagging
            for mtk, tk in zip(msent, tsent):
                tk.pos = mtk.pos3()
                tk.new_tag(mtk.pos3(), tagtype='pos', source=ttl.Tag.MECAB)
                tk.new_tag(mtk.reading_hira(), tagtype="Reading", source=ttl.Tag.MECAB)
        # sense tagging
        doc[2][4].comment = 'to eat'
        doc[0].new_concept("三毛猫", "wiki.ja:三毛猫", tokens=[0, 1, 2]).comment = 'Calico cat, you know?'
        doc[1].new_concept("降る", "02756821-v", tokens=(2,))
        doc[2].new_concept("女の子", "10084295-n", tokens=(0,))
        doc[2].new_concept("食べる", "01166351-v", (4,))
        # tags
        doc[0].new_tag("WIKI", 0, 3, tagtype="SRC")
        doc[0].new_tag("https://ja.wikipedia.org/wiki/三毛猫", 0, 3, tagtype="URL")
        doc[2].new_tag("WIKI", 0, 3, tagtype="SRC")
        doc[2].new_tag("https://ja.wikipedia.org/wiki/少女", 0, 3, tagtype="URL")
        # export doc
        doc.write_ttl_streams(sents.file, words.file, concepts.file, links.file, tags.file)
        getLogger().debug("sents\n{}".format(sents.content()))
        getLogger().debug("words\n{}".format(words.content()))
        getLogger().debug("concepts\n{}".format(concepts.content()))
        getLogger().debug("links\n{}".format(links.content()))
        getLogger().debug("tags\n{}".format(tags.content()))
        self.assertTrue(sents.content())
        self.assertTrue(words.content())
        self.assertTrue(concepts.content())
        self.assertTrue(links.content())
        self.assertTrue(tags.content())


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
