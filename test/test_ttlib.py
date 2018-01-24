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
from chirptext.texttaglib import TagInfo, TaggedSentence, TaggedDoc, Token
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
        doc = TaggedDoc(TEST_DATA, 'test')
        # add words
        sent = doc.add_sent('Some happy guard-dogs barked.', 1)
        sent.import_tokens('Some happy guard dogs barked .'.split())
        self.assertEqual(len(sent), 6)
        # sense tagging
        sent.add_concept(0, 'happy', '01148283-a', [sent[1]])
        sent.add_concept(1, 'dog', '02084071-n')
        sent.concept(1).add_word(sent[3])
        sent.tag('bark', BARK_SID, 4)
        sent.tag('guard-dog', GDOG_SID, 2, 3)  # MWE example
        # verification
        wcl = sent.wclinks
        self.assertEqual(wcl[sent[3]][0].clemma, 'dog')
        self.assertEqual(wcl[sent[3]][1].clemma, 'guard-dog')
        self.assertEqual(wcl[sent[3]][1].tag, GDOG_SID)
        self.assertEqual(wcl[sent[4]][0].tag, BARK_SID)
        self.assertTrue(sent.mwe)
        self.assertEqual(sent.mwe[0].tag, GDOG_SID)


class TestTagging(unittest.TestCase):

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

    def test_tag_token(self):
        token = Token(0, 4, "Words")
        token.tag("n", tagtype="pos")
        token.tag("plural")
        token.tag("word-token")
        token.tag("word", tagtype="lemma")
        token.tag("Words", tagtype="lemma")
        token.tag("an element of speech or writing", tagtype="comment")
        js_token = token.to_json()
        expected = {"tags": {"unsorted": ["plural", "word-token"]}, "cfrom": 0, "pos": "n", "cto": 4, "label": "Words", "lemma": "word, Words", 'comment': 'an element of speech or writing'}
        self.assertEqual(js_token, expected)

    def test_comment(self):
        sent = TaggedSentence("Dogs bark.")
        sent.import_tokens("Dogs bark .".split())
        sent[0].tag("canine", tagtype="comment")
        sent.tag("02084071-n", "dog", 0)
        sent.concepts[0].comment = 'a member of the genus Canis (probably descended from the common wolf) that has been domesticated by man since prehistoric times'
        expected = {'text': 'Dogs bark.', 'tokens': [{'cto': 4, 'cfrom': 0, 'comment': 'canine', 'label': 'Dogs'}, {'cto': 9, 'cfrom': 5, 'label': 'bark'}, {'cto': 10, 'cfrom': 9, 'label': '.'}], 'concepts': [{'tag': 'dog', 'clemma': '02084071-n', 'comment': 'a member of the genus Canis (probably descended from the common wolf) that has been domesticated by man since prehistoric times', 'words': [0]}]}
        self.assertEqual(expected, sent.to_json())
        self.assertFalse(sent.tags)
        sent.add_tag(GDOG_SID, 0, 4, tagtype='wn30')
        sent.add_tag(BARK_SID, 5, 9, tagtype='wn30')
        for t in sent.tags:
            getLogger().debug("{}: label={} | type = {}".format(t, t.label, t.tagtype))

    def test_tagged_sentences(self):
        sent = TaggedSentence('猫が好きです 。')
        mecab_sent = txt2mecab(sent.text)
        # import tags
        sent.import_tokens(mecab_sent.words)
        for mtoken, token in zip(mecab_sent, sent.tokens):
            if mtoken.reading_hira() != token.label:
                if token.label in ('猫', '好き'):
                    token.tag(mtoken.reading_hira(), tagtype=Token.LEMMA)
                token.tag(mtoken.reading_hira())
                token.tag(mtoken.pos3(), tagtype="pos")
        self.assertEqual(mecab_sent.words, [x.label for x in sent.tokens])
        self.assertEqual(sent.tokens[0].tags[0].label, 'ねこ')
        self.assertEqual(sent.tokens[0].lemma, 'ねこ')
        self.assertEqual(sent.tokens[2].tags[0].label, 'すき')
        self.assertEqual(sent.tokens[3].lemma, '')  # if there is no lemma label => return ''
        self.assertEqual(sent.tokens[2].surface, '好き')
        self.assertFalse(sent.tokens[1].tags)
        self.assertFalse(sent.tokens[3].tags)
        self.assertFalse(sent.tokens[4].tags)
        return sent

    def test_tagged_sent_to_json(self):
        sent = TaggedSentence("女の子は猫が好きです。")
        sent.import_tokens("女 の 子 は 猫 が 好き です 。".split())
        sent[0].tag("おんな", tagtype="lemma")
        sent[2].tag("こ", tagtype="lemma")
        sent[4].tag("ねこ", tagtype="lemma")
        sent[4].tag("Say neh-koh", tagtype="comment")
        sent[4].tag("名詞-一般", tagtype="pos")
        sent[6].tag("すき", tagtype="lemma")
        sent[6].tag("名詞-形容動詞語幹", tagtype="pos")
        sent.tag("女の子", " 10084295-n", 0, 1, 2)
        sent.concepts[0].comment = "若々しい女の人"
        sent.tag("猫", "02121620-n", 4)
        sent.tag("好き", "01292683-a", 6)
        expected = {'tokens': [{'cfrom': 0, 'cto': 1, 'lemma': 'おんな', 'label': '女'}, {'cfrom': 1, 'cto': 2, 'label': 'の'}, {'cfrom': 2, 'cto': 3, 'lemma': 'こ', 'label': '子'}, {'cfrom': 3, 'cto': 4, 'label': 'は'}, {'pos': '名詞-一般', 'cfrom': 4, 'cto': 5, 'lemma': 'ねこ', 'label': '猫', 'comment': 'Say neh-koh'}, {'cfrom': 5, 'cto': 6, 'label': 'が'}, {'pos': '名詞-形容動詞語幹', 'cfrom': 6, 'cto': 8, 'lemma': 'すき', 'label': '好き'}, {'cfrom': 8, 'cto': 10, 'label': 'です'}, {'cfrom': 10, 'cto': 11, 'label': '。'}], 'text': '女の子は猫が好きです。', 'concepts': [{'tag': ' 10084295-n', 'words': [0, 1, 2], 'clemma': '女の子', 'comment': '若々しい女の人'}, {'tag': '02121620-n', 'words': [4], 'clemma': '猫'}, {'tag': '01292683-a', 'words': [6], 'clemma': '好き'}]}
        actual = sent.to_json()
        self.assertEqual(expected, actual)

    def test_json_tagged_sent(self):
        raw = {'tokens': [{'cfrom': 0, 'cto': 1, 'lemma': 'おんな', 'label': '女'}, {'cfrom': 1, 'cto': 2, 'label': 'の'}, {'cfrom': 2, 'cto': 3, 'lemma': 'こ', 'label': '子'}, {'cfrom': 3, 'cto': 4, 'label': 'は'}, {'pos': '名詞-一般', 'cfrom': 4, 'cto': 5, 'lemma': 'ねこ', 'label': '猫', 'comment': 'Say neh-koh'}, {'cfrom': 5, 'cto': 6, 'label': 'が'}, {'pos': '名詞-形容動詞語幹', 'cfrom': 6, 'cto': 8, 'lemma': 'すき', 'label': '好き'}, {'cfrom': 8, 'cto': 10, 'label': 'です'}, {'cfrom': 10, 'cto': 11, 'label': '。'}], 'text': '女の子は猫が好きです。', 'concepts': [{'tag': ' 10084295-n', 'words': [0, 1, 2], 'clemma': '女の子', 'comment': '若々しい女の人', 'flag': 'G'}, {'tag': '02121620-n', 'words': [4], 'clemma': '猫'}, {'tag': '01292683-a', 'words': [6], 'clemma': '好き'}]}
        # json => TaggedSentence => json
        sent = TaggedSentence.from_json(raw)
        sent_json = sent.to_json()
        self.assertEqual(raw, sent_json)
        self.assertEqual(sent_json['concepts'][0]['flag'], 'G')
        pass

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

    def test_cwl(self):
        doc = TaggedDoc(TEST_DATA, 'test').read()
        sent = doc[0]
        # ensure that words and concepts are linked properly
        w = doc[0][-4]
        c = sent.wclinks[w][0]
        tag = w.tag_map['pos'][0]
        self.assertEqual(tag.label, 'WP')
        self.assertEqual(w.pos, 'WP')  # shortcut for POS
        self.assertEqual(c.words[0].tag_map['pos'][0].label, 'WP')
        tag.label = 'x'
        self.assertEqual(c.words[0].tag_map['pos'][0].label, 'x')
        # test sentence level tagging
        getLogger().debug([str(t) for t in sent.tags])

    def test_multiple_tags(self):
        doc = TaggedDoc(TEST_DATA, 'test').read()
        mw_ms = [(len(s.mwe), len(s.msw)) for s in doc]
        self.assertEqual(mw_ms, [(2, 2), (0, 0), (3, 2)])

    def test_recover_surface_string(self):
        s = TaggedSentence('''a religious sect founded in the United States in 1966; based on Vedic scriptures; groups engage in joyful chanting of `Hare Krishna' and other mantras based on the name of the Hindu god Krishna; devotees usually wear saffron robes and practice vegetarianism and celibacy''')
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
        doc = TaggedDoc(TEST_DATA, 'manual')
        # create sents in doc
        raws = ("三毛猫がすきです。", "雨が降る。", "女の子はケーキを食べる。")
        for sid, r in enumerate(raws):
            msent = txt2mecab(r)
            tsent = doc.add_sent(msent.surface, sid)
            tsent.import_tokens(msent.words)
            # pos tagging
            for mtk, tk in zip(msent, tsent):
                tk.tag(mtk.pos3(), tagtype=Token.POS, source=TagInfo.MECAB)
                tk.tag(mtk.reading_hira(), tagtype=Token.LEMMA, source=TagInfo.MECAB)
        # sense tagging
        doc[0].tag("三毛猫", "wiki.ja:三毛猫", 0, 1, 2)
        doc[1].tag("降る", "02756821-v", 2)
        doc[2].tag("女の子", "10084295-n", 0)
        doc[2].tag("食べる", "01166351-v", 4)
        # tags
        doc[0].add_tag("WIKI", 0, 3, tagtype="SRC")
        doc[0].add_tag("https://ja.wikipedia.org/wiki/三毛猫", 0, 3, tagtype="URL")
        doc[2].add_tag("WIKI", 0, 3, tagtype="SRC")
        doc[2].add_tag("https://ja.wikipedia.org/wiki/少女", 0, 3, tagtype="URL")
        # export doc
        doc.export(sents.file, words.file, concepts.file, links.file, tags.file)
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
