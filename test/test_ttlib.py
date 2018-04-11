#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Script for testing leutile

Latest version can be found at https://github.com/letuananh/chirptext

:copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
:license: MIT, see LICENSE for more details.
'''

import os
import io
import unittest
import logging
import json
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

class TestBasicModel(unittest.TestCase):

    def test_sentid(self):
        doc = ttl.Document('mydoc')
        sent = doc.new_sent('First sentence.')
        self.assertEqual(sent.ID, 1)
        sent2 = doc.new_sent('Second sentence.')
        self.assertEqual(sent2.ID, 2)
        # add some sentences manually
        sentm1 = ttl.Sentence('Another one', ID=3)
        sentm2 = ttl.Sentence('Another one 2', ID='5')
        doc.add_sent(sentm1)
        doc.add_sent(sentm2)
        doc.new_sent('Third sentence.')
        doc.new_sent('Fourth sentence.')
        sent5 = doc.new_sent('Fifth sentence.')
        self.assertEqual(sent5.ID, 7)
        # cannot add 3 again
        sent_foo = ttl.Sentence('Foo sentence.', ID=3)
        self.assertRaises(Exception, lambda: doc.add_sent(sent_foo))
        # cannot add a None sentence
        self.assertRaises(Exception, lambda: doc.add_sent(None))
        # document should have 5 created sentences + 2 imported sentences
        self.assertEqual(len(doc), 7)

    def test_extra_fields(self):
        cmt = 'This sentence is in English'
        s = ttl.Sentence(text='I am a sentence.', docID=1, comment=cmt)
        self.assertEqual(s.docID, 1)
        self.assertEqual(s.comment, cmt)


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
        sent.concept(c.cidx).add_token(sent[3])
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
        self.assertEqual(t2.source, ttl.Tag.NONE)

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

    def import_tokens(self, sent, token_list):
        sent.tokens = token_list

    def test_import_tokens(self):
        sent = ttl.Sentence('It rains.')
        tokens = ['It', 'rains', '.']
        sent.tokens = tokens
        self.assertEqual([t.text for t in sent.tokens], tokens)
        # cannot import twice
        self.assertRaises(Exception, lambda: self.import_tokens(sent, tokens))
        # or import half-way
        sent2 = ttl.Sentence("Cats don't like cats that meow.")
        sent2.import_tokens(('Cats',))
        tokens2 = "do n't like cats that meow .".split()
        self.assertRaises(Exception, lambda: self.import_tokens(sent, tokens2))
        sent2.import_tokens(tokens2)  # but use import_tokens explicitly is fine
        self.assertEqual([t.text for t in sent2.tokens], ['Cats', 'do', "n't", 'like', 'cats', 'that', 'meow', '.'])

    def test_comment(self):
        sent = ttl.Sentence("Dogs bark.")
        sent.import_tokens("Dogs bark .".split())
        sent[0].comment = "canine"
        sent.new_concept("02084071-n", "dog", tokens=(sent[0],))
        sent.concepts[0].comment = 'a member of the genus Canis (probably descended from the common wolf) that has been domesticated by man since prehistoric times'
        expected = {'text': 'Dogs bark.', 'tokens': [{'cto': 4, 'cfrom': 0, 'comment': 'canine', 'text': 'Dogs'}, {'cto': 9, 'cfrom': 5, 'text': 'bark'}, {'cto': 10, 'cfrom': 9, 'text': '.'}], 'concepts': [{'tag': '02084071-n', 'clemma': 'dog', 'comment': 'a member of the genus Canis (probably descended from the common wolf) that has been domesticated by man since prehistoric times', 'tokens': [0]}]}
        getLogger().debug(sent.to_json())
        getLogger().debug(expected)
        self.assertEqual(expected, sent.to_json())
        self.assertFalse(sent.tags)
        sent.new_tag(GDOG_SID, 0, 4, tagtype='wn30')
        sent.new_tag(BARK_SID, 5, 9, tagtype='wn30')
        for t in sent.tags:
            getLogger().debug("{}: label={} | type = {}".format(t, t.label, t.tagtype))

    def test_tagged_sentences(self):
        print("test converting MeCabSent into TTL Sent manually")
        sent = ttl.Sentence('猫が好きです 。')
        mecab_sent = txt2mecab(sent.text)
        getLogger().debug((mecab_sent.surface, mecab_sent.words))
        # import tags
        sent.import_tokens(mecab_sent.words)
        for mtoken, token in zip(mecab_sent, sent.tokens):
            if mtoken.reading_hira() != token.text:
                if token.text in ('猫', '好き'):
                    token.new_tag(mtoken.reading_hira(), tagtype='reading')
                token.lemma = mtoken.reading_hira()
                token.pos = mtoken.pos3()
        self.assertEqual(mecab_sent.words, [x.text for x in sent.tokens])
        self.assertEqual(sent[0].find('reading').label, 'ねこ')
        self.assertEqual(sent[0].lemma, 'ねこ')
        self.assertEqual(sent[2][0].label, 'すき')
        self.assertFalse(sent[3].lemma, '')  # if there is no lemma label => return ''
        self.assertEqual(sent[2].surface(), '好き')
        self.assertFalse(len(sent[1]))
        self.assertFalse(len(sent[3]))
        self.assertFalse(len(sent[4]))
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
        getLogger().debug(actual)

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
        doc = ttl.Document('manual', TEST_DATA)
        # create sents in doc
        raws = ("三毛猫が好きです。", "雨が降る。", "女の子はケーキを食べる。")
        for sid, r in enumerate(raws):
            msent = txt2mecab(r)
            tsent = doc.new_sent(msent.surface, sid)
            tsent.import_tokens(msent.words)
            # pos tagging
            for mtk, tk in zip(msent, tsent):
                tk.pos = mtk.pos3()
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
        concepts = TextReport.string()
        links = TextReport.string()
        sents = TextReport.string()
        tags = TextReport.string()
        words = TextReport.string()
        writer = ttl.TxtWriter(sents.file, words.file, concepts.file, links.file, tags.file)
        writer.write_doc(doc)
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
        for sent in doc:
            logging.debug(json.dumps(sent.to_json(), ensure_ascii=False))


class TestJSON(unittest.TestCase):
    def test_tags(self):
        sent = ttl.Sentence('三毛猫が好きです。')
        sent.flag = '0'
        sent.comment = 'written in Japanese'
        sent.new_tag('I like calico cats.', tagtype='eng')
        sent.import_tokens('三 毛 猫 が 好き です 。'.split())
        for tk, pos in zip(sent, '名詞 名詞 名詞 助詞 名詞 助動詞 記号'.split()):
            tk.pos = pos
        sent.new_concept("三毛猫", "wiki.ja:三毛猫", tokens=[0, 1, 2])
        sent[0].new_tag('mi', tagtype='reading')
        sent[1].new_tag('ke', tagtype='reading')
        sent[2].new_tag('neko', tagtype='reading')
        getLogger().debug(sent.to_json())
        concepts = TextReport.string()
        links = TextReport.string()
        sents = TextReport.string()
        tags = TextReport.string()
        words = TextReport.string()
        writer = ttl.TxtWriter(sents.file, words.file, concepts.file, links.file, tags.file)
        writer.write_sent(sent)
        sents_txt = sents.content()
        words_txt = words.content()
        concepts_txt = concepts.content()
        links_txt = links.content()
        tags_txt = tags.content()
        getLogger().debug("sents\n{}".format(sents_txt))
        getLogger().debug("words\n{}".format(words_txt))
        getLogger().debug("concepts\n{}".format(concepts_txt))
        getLogger().debug("links\n{}".format(links_txt))
        getLogger().debug("tags\n{}".format(tags_txt))
        # read it back
        reader = ttl.TxtReader(io.StringIO(sents_txt),
                               io.StringIO(words_txt),
                               io.StringIO(concepts_txt),
                               io.StringIO(links_txt),
                               io.StringIO(tags_txt))
        docx = reader.read()
        # patch sent.ID
        sent.ID = 1
        jo = sent.to_json()
        jr = docx[0].to_json()
        getLogger().debug(jo)
        getLogger().debug(jr)
        self.assertEqual(jo['text'], jr['text'])
        self.assertEqual(jo['tokens'], jr['tokens'])
        self.assertEqual(jo['concepts'], jr['concepts'])
        self.assertEqual(jo['tags'], jr['tags'])
        self.assertEqual(jo['flag'], jr['flag'])
        self.assertEqual(jo['comment'], jr['comment'])
        self.assertEqual(jo, jr)


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
