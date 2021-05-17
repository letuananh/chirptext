#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script for testing leutile

Latest version can be found at https://github.com/letuananh/chirptext

:copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
:license: MIT, see LICENSE for more details.
"""
import collections
import os
import io
import unittest
from collections import Set
import logging
import json
from chirptext import TextReport
from chirptext import ttl
from chirptext import deko

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

TEST_DIR = os.path.dirname(__file__)
TEST_DATA = os.path.join(TEST_DIR, 'data')
TEST_FILE = os.path.join(TEST_DATA, 'test')

BARK_SID = '01047745-v'
GDOG_SID = '02103841-n'

sent1 = "三毛猫が好きです。"
sent2 = "雨が降る。"
sent3 = "女の子はケーキを食べる。"
sent4 = "猫が好きです 。"
sent1_mecab = '三\t名詞,数,*,*,*,*,三,サン,サン\n毛\t名詞,接尾,助数詞,*,*,*,毛,モウ,モー\n猫\t名詞,一般,*,*,*,*,猫,ネコ,ネコ\nが\t助詞,格助詞,一般,*,*,*,が,ガ,ガ\n好き\t名詞,形容動詞語幹,*,*,*,*,好き,スキ,スキ\nです\t助動詞,*,*,*,特殊・デス,基本形,です,デス,デス\n。\t記号,句点,*,*,*,*,。,。,。\nEOS'
sent2_mecab = '雨\t名詞,一般,*,*,*,*,雨,アメ,アメ\nが\t助詞,格助詞,一般,*,*,*,が,ガ,ガ\n降る\t動詞,自立,*,*,五段・ラ行,基本形,降る,フル,フル\n。\t記号,句点,*,*,*,*,。,。,。\nEOS'
sent3_mecab = '女の子\t名詞,一般,*,*,*,*,女の子,オンナノコ,オンナノコ\nは\t助詞,係助詞,*,*,*,*,は,ハ,ワ\nケーキ\t名詞,一般,*,*,*,*,ケーキ,ケーキ,ケーキ\nを\t助詞,格助詞,一般,*,*,*,を,ヲ,ヲ\n食べる\t動詞,自立,*,*,一段,基本形,食べる,タベル,タベル\n。\t記号,句点,*,*,*,*,。,。,。\nEOS'
sent4_mecab = '猫\t名詞,一般,*,*,*,*,猫,ネコ,ネコ\nが\t助詞,格助詞,一般,*,*,*,が,ガ,ガ\n好き\t名詞,形容動詞語幹,*,*,*,*,好き,スキ,スキ\nです\t助動詞,*,*,*,特殊・デス,基本形,です,デス,デス\n。\t記号,句点,*,*,*,*,。,。,。\nEOS'


def getLogger():
    return logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------------------
class TestBasicModel(unittest.TestCase):

    def test_tagset(self):
        tags = ttl.TagSet()
        tags.new("NN", "pos", source="manual")
        self.assertTrue(len(tags.pos), 1)
        self.assertIsInstance(tags.pos, ttl.ProtoList)
        self.assertIsInstance(tags.pos[0], ttl.Tag)
        self.assertEqual(tags.gold.pos.value, "NN")
        self.assertEqual(tags.gold.pos.type, "pos")
        self.assertEqual(tags.gold.pos.source, "manual")
        # replace tag
        tags.gold.pos = "NNP"
        self.assertTrue(len(tags.pos), 1)  # still at 1, because we reset it
        self.assertEqual(tags.gold.pos.value, "NNP")
        self.assertEqual(tags.gold.pos.type, "pos")
        self.assertEqual(tags.gold.pos.source, "")  # source should be empty because this is a new tag

        # tag type should be read only
        def _func():
            tags.gold.pos.type = "POS"

        self.assertRaises(AttributeError, lambda: _func())
        # test attr access and key access
        self.assertEqual(tags.gold.pos, tags.gold["pos"])
        self.assertEqual(tags.pos, tags["pos"])

    def test_mixing_gold_and_list_access(self):
        tags = ttl.TagSet()
        # add another POS
        tags.new("cat-n-1", "sense")
        pos1 = tags.pos.new("NNP")
        tags.new("cat-n-2", "sense")
        tags.new("cat-n-3", "sense")
        pos2 = tags.new("NN", "pos")
        self.assertEqual(len(tags.pos), 2)
        tags.gold.sense = "cat-n-4"  # set the best sense to cat-n-4
        self.assertEqual(len(tags.sense), 3)
        actual = set(tags.values('pos'))
        expected = {"NNP", "NN"}
        self.assertEqual(expected, actual)
        actual = set(tags.values())
        expected = {"NNP", "NN",
                    "cat-n-2", "cat-n-3", "cat-n-4"}
        self.assertEqual(expected, actual)

    def test_comparing_token_list(self):
        set1 = ttl.TokenList()
        set2 = ttl.TokenList()
        self.assertEqual(set1, set2)
        t = ttl.Token("a")
        set1.append(t)
        set2.append(t)
        self.assertEqual(set1, set2)
        t2 = ttl.Token("word")
        set2.append(t2)
        self.assertNotEqual(set1, set2)
        t3 = ttl.Token("word")
        set1.append(t3)
        # TODO: deep comparing? (may be not)
        self.assertNotEqual(set1, set2)

    def test_tag_model(self):
        ssid = '06162979-n'
        tag = ttl.Tag(ssid, type='PWN30')
        self.assertEqual(tag.type, 'PWN30')
        self.assertEqual(tag.type, 'PWN30')
        self.assertEqual(tag.text, ssid)
        self.assertEqual(tag.value, ssid)
        tag.value = '00636921-n'
        self.assertEqual(tag.text, '00636921-n')

        def _func():
            tag.type = 'OMW1.2'

        self.assertRaises(AttributeError, lambda: _func())
        self.assertEqual(tag.type, 'PWN30')  # tag type should still be PWN30 because tag type are immutable
        self.assertEqual(tag.to_dict(), {'value': '00636921-n', 'type': 'PWN30'})
        # tag can be non-typed
        tag_foo = ttl.Tag('foo')
        tag_foo.source = '頭'
        self.assertEqual(repr(tag_foo), "Tag(value='foo')")
        self.assertEqual(tag_foo.to_dict(), {'value': 'foo', 'source': '頭'})
        t = ttl.Tag("nontype", None)  # set type to None explicitly
        self.assertEqual(t.type, '')  # tag type cannot be None, it can only be empty
        self.assertEqual(t.to_dict(), {'value': 'nontype'})
        # or can be typed with an empty value (either None or ''
        t = ttl.Tag(None, "speaker")
        self.assertEqual(ttl.Tag.from_dict(t.to_dict()).to_dict(), {'type': 'speaker', 'value': None})
        self.assertEqual(t.text, '')  # text property returns '' when value is None
        t.value = ''
        self.assertEqual(ttl.Tag.from_dict(t.to_dict()).to_dict(), {'type': 'speaker', 'value': ''})
        t.value = None
        self.assertEqual(t.value, None)
        self.assertEqual(t.text, '')  # text property returns '' when value is None
        # from_json
        tag_json = {'value': 'foo', 'source': '頭', 'type': '冗談', 'cfrom': 0, 'cto': 3}
        tag_new = ttl.Tag.from_dict(tag_json)
        self.assertEqual(tag_json, tag_new.to_dict())

    def test_get_or_create(self):
        ts = ttl.TagSet()
        t = ts.gold.get_or_create("pos", "NN")
        self.assertEqual(t.to_dict(), {'type': 'pos', 'value': 'NN'})
        # now it is created, default values should not be used any more
        t2 = ts.gold.get_or_create("pos", "NNP")
        self.assertEqual(t2.to_dict(), {'type': 'pos', 'value': 'NN'})

    def test_sentid(self):
        doc = ttl.Document('mydoc')
        sent = doc.sents.new('First sentence.')
        self.assertEqual(sent.ID, "1")
        sent2 = doc.sents.new('Second sentence.')
        self.assertEqual(sent2.ID, "2")
        # add some sentences manually
        sentm1 = ttl.Sentence('Another one', ID=3)
        sentm2 = ttl.Sentence('Another one 2', ID='5')
        doc.sents.append(sentm1)
        doc.sents.append(sentm2)
        doc.sents.new('Third sentence.')
        doc.sents.new('Fourth sentence.')
        sent5 = doc.sents.new('Fifth sentence.')
        self.assertEqual(sent5.ID, "7")
        # cannot add 3 again
        sent_foo = ttl.Sentence('Foo sentence.', ID=3)
        self.assertRaises(Exception, lambda: doc._add_sent_obj(sent_foo))
        # cannot add a None sentence
        self.assertRaises(Exception, lambda: doc._add_sent_obj(None))
        # document should have 5 created sentences + 2 imported sentences
        self.assertEqual(len(doc), 7)

    def test_extra_fields(self):
        cmt = 'This sentence is in English'
        s = ttl.Sentence(text='I am a sentence.', docID=1, comment=cmt)
        self.assertEqual(s.docID, 1)
        self.assertEqual(s.comment, cmt)

    def test_creating_sent(self):
        tokens = 'It rains .'.split()
        s = ttl.Sentence('It rains.', tokens=tokens)
        self.assertEqual([t.text for t in s.tokens], tokens)
        self.assertEqual(repr(s), "Sentence('It rains.')")
        self.assertEqual(str(s), s.text)
        self.assertEqual(s.surface(s[0]), 'It')
        self.assertEqual(s.surface(ttl.Tag(cfrom=-1, cto=-1)), '')
        self.assertEqual(s.surface(ttl.Tag(cfrom=-1, cto=3)), '')
        self.assertEqual(s.surface(ttl.Tag(cfrom=3, cto=-1)), '')
        self.assertEqual(s.surface(ttl.Tag(cfrom=None, cto=None)), '')
        s.ID = '1'
        self.assertEqual(repr(s), "Sentence(ID='1', text='It rains.')")
        self.assertEqual(str(s), s.text)
        # tag sentence
        url = 'https://github.com/letuananh/chirptext'
        s.tag.URL = url
        self.assertEqual(s.tag['URL'].text, url)
        self.assertEqual(s.tag['URL'].value, url)
        self.assertEqual(len(s.tags.URL), 1)
        self.assertEqual(list(s.tags.values('URL')), [url])
        # test concepts
        c = s.concepts.new(value='02756558-v', clemma='rain')
        self.assertRaises(Exception, lambda: s.concepts.new(None))
        self.assertRaises(Exception, lambda: s.concepts.new(''))
        c2 = s.concepts.new(value='dummy', clemma='it')
        self.assertEqual(len(s.concepts), 2)
        self.assertRaises(Exception, lambda: s.concept.remove(3))
        self.assertEqual(s.concepts.remove(c2), c2)
        self.assertEqual(list(s.concepts), [c])

    def test_idgen(self):
        idg = ttl.IDGenerator()
        _ids = [next(idg) for i in range(3)]
        idg_explicit = ttl.IDGenerator(id_seed=1)
        _ids2 = [next(idg_explicit) for i in range(3)]
        expected = [1, 2, 3]
        self.assertEqual(_ids, expected)
        self.assertEqual(_ids2, expected)


class TestBuildTags(unittest.TestCase):

    def test_create_sent(self):
        doc = ttl.Document('test', TEST_DATA)
        # add words
        sent = doc.sents.new('Some happy guard-dogs barked.', 1)
        sent._import_tokens('Some happy guard dogs barked .'.split())
        self.assertEqual(len(sent), 6)
        # sense tagging
        sent.concepts.new('01148283-a', 'wn', clemma='happy', tokens=[sent[1]])
        # create a new concept and then bind a token in
        c = sent.concepts.new('02084071-n', 'wn', 'dog')
        c.tokens.append(sent[3])
        sent.concepts.new(BARK_SID, "wn", 'bark').tokens.append(sent[4])  # add token object
        sent.concepts.new(GDOG_SID, "wn", 'guard-dog').tokens = (2, 3)  # MWE example, add by index
        # verification
        tcmap = sent.tcmap()
        self.assertEqual(tcmap[sent[3]][0].clemma, 'dog')
        self.assertEqual(tcmap[sent[3]][1].clemma, 'guard-dog')
        self.assertEqual(tcmap[sent[3]][1].value, GDOG_SID)
        self.assertEqual(tcmap[sent[4]][0].value, BARK_SID)
        mwe = list(sent.mwe())
        self.assertTrue(mwe)
        self.assertEqual(mwe[0].value, GDOG_SID)

    def test_sentids(self):
        doc = ttl.Document('boo')
        s = ttl.Sentence('odd', ID=3)
        self.assertEqual(s.ID, "3")
        doc.sents.append(s)  # add sent#3 first
        doc.sents.new('foo')  # 1
        doc.sents.new('boo')  # 2
        moo = doc.sents.new('moo')  # moo will be #4 because sent #3 exists
        self.assertEqual(moo.ID, "4")
        sids = [s.ID for s in doc]
        self.assertEqual(sids, ["3", "1", "2", "4"])


class TestComment(unittest.TestCase):
    """ Ensure that all objects may hold comments and flags """

    def test_storing_flags(self):
        doc = ttl.read(TEST_FILE)
        sent = doc["10315"]  # use sentence #10315 for testing
        # before setting concept
        sent.flag = ttl.Tag.GOLD  # setting sentence flag
        sent[0].flag = ttl.Tag.NLTK  # flag the first token with NLTK
        # create a concept with tokens
        sent.concept.wn = "Wordnet 3.0"
        sent.concept.wn.flag = ttl.Tag.ISF
        sent.concept.wn.tokens.append(1)
        sent_json = sent.to_dict()
        self.assertEqual(sent_json['flag'], ttl.Tag.GOLD)
        self.assertEqual(sent_json['tokens'][0]['flag'], ttl.Tag.NLTK)
        self.assertEqual(sent_json['concepts'][-1]['flag'], ttl.Tag.ISF)


class TestTagging(unittest.TestCase):

    def test_taginfo(self):
        t = ttl.Tag('dog', cfrom=1, cto=4, source=ttl.Tag.ISF)
        self.assertEqual(t.cfrom, 1)
        self.assertEqual(t.cto, 4)
        self.assertEqual(t.value, 'dog')
        self.assertEqual(t.source, ttl.Tag.ISF)

        # Source = DEFAULT now
        t2 = ttl.Tag('bark', cfrom=0, cto=5)
        self.assertEqual(t2.cfrom, 0)
        self.assertEqual(t2.cto, 5)
        self.assertEqual(t2.value, 'bark')
        self.assertEqual(t2.source, ttl.Tag.NONE)

    def test_tag_token(self):
        token = ttl.Token("Words", 0, 4)
        token.tag.count = "plural"
        token.tag.type = "word-token"
        token.tags.new("no type just value")
        self.assertRaises(ValueError, lambda: token.tags.new(None))
        token.pos = 'n'
        token.lemma = 'word'
        token.comment = "an element of speech or writing"
        js_token = token.to_dict()
        getLogger().debug(js_token)
        expected = {'cfrom': 0, 'cto': 4, 'text': 'Words',
                    'lemma': 'word', 'pos': 'n', 'comment': 'an element of speech or writing',
                    'tags': [{'value': 'plural', 'type': 'count'},
                             {'value': 'word-token', 'type': 'type'},
                             {'value': 'no type just value'}]}
        self.assertEqual(js_token, expected)

    def test_tag_type_and_searching(self):
        taggable_objects = [
            ttl.Token("text", 0, 4),
            ttl.Sentence('I am a sentence.')
        ]
        for obj in taggable_objects:
            obj.tags.new("06387980-n", type="synset")
            obj.tags.new("06414372-n", type="synset")
            obj.tags.new("manual", type="tagtype")
            # find all values by types
            synsets = list(obj.tags.values("synset"))
            self.assertEqual(synsets, ["06387980-n", "06414372-n"])
            # find a specific tag
            self.assertEqual(obj.tag.tagtype.text, "manual")
            self.assertEqual(obj.tag['tagtype'].text, "manual")
            # auto create ..
            self.assertEqual(obj.tag.get_or_create('meaning', default='N/A').value, "N/A")
            self.assertEqual(obj.tag.meaning.text, "N/A")

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
        sent2._import_tokens(('Cats',))
        tokens2 = "do n't like cats that meow .".split()
        self.assertRaises(Exception, lambda: self.import_tokens(sent, tokens2))
        sent2._import_tokens(tokens2)  # but use import_tokens explicitly is fine
        self.assertEqual([t.text for t in sent2.tokens], ['Cats', 'do', "n't", 'like', 'cats', 'that', 'meow', '.'])

    def test_comment(self):
        sent = ttl.Sentence("Dogs bark.")
        sent._import_tokens("Dogs bark .".split())
        sent.comment = 'I am a test sentence.'
        sent[0].comment = "canine"
        sent.concepts.new("02084071-n", clemma="dog", tokens=(sent[0],))

        list(sent.concepts)[0].comment = 'a member of the genus Canis (probably descended from the common wolf) that has been domesticated by man since prehistoric times'
        expected = {'text': 'Dogs bark.', 'comment': 'I am a test sentence.',
                    'tokens': [{'cto': 4, 'cfrom': 0, 'comment': 'canine', 'text': 'Dogs'},
                               {'cto': 9, 'cfrom': 5, 'text': 'bark'},
                               {'cto': 10, 'cfrom': 9, 'text': '.'}],
                    'concepts': [{'value': '02084071-n', 'clemma': 'dog', 'comment': 'a member of the genus Canis (probably descended from the common wolf) that has been domesticated by man since prehistoric times', 'tokens': [0]}]}
        getLogger().debug(sent.to_dict())
        getLogger().debug(expected)
        self.assertEqual(expected, sent.to_dict())
        self.assertFalse(sent.tags)
        sent.tags.new(GDOG_SID, 'wn30', 0, 4)
        sent.tag.wn30 = {"value": BARK_SID, "cfrom": 5, "cto": 9}
        for t in sent.tags:
            getLogger().debug("{}: label={} | type = {}".format(t, t.value, t.type))

    def test_tagged_sentences(self):
        print("test converting MeCabSent into TTL Sent manually")
        sent = ttl.Sentence('猫が好きです 。')
        mecab_sent = deko.mecab._mecab_output_to_sent(sent4, sent4_mecab)
        # import tags
        sent._import_tokens(mecab_sent.tokens.values())
        for mtoken, token in zip(mecab_sent, sent.tokens):
            if mtoken.reading_hira != token.text:
                if token.text in ('猫', '好き'):
                    token.tag.reading = mtoken.reading_hira
                token.lemma = mtoken.reading_hira
                token.pos = mtoken.pos3
        self.assertEqual(mecab_sent.tokens.values(), [x.text for x in sent.tokens])
        self.assertEqual(sent[0].tag.reading.value, 'ねこ')
        self.assertEqual(sent[0].lemma, 'ねこ')
        self.assertEqual(sent[2].tag.reading.value, 'すき')  # accessing gold-value
        self.assertFalse(sent[3].lemma, '')  # if there is no lemma label => return ''
        self.assertEqual(sent[2].surface(), '好き')
        self.assertFalse(len(sent[1]))
        self.assertFalse(len(sent[3]))
        self.assertFalse(len(sent[4]))
        return sent

    def test_tagged_sent_to_json(self):
        sent = ttl.Sentence("女の子は猫が好きです。")
        sent._import_tokens("女 の 子 は 猫 が 好き です 。".split())
        sent[0].lemma = "おんな"
        sent[2].lemma = "こ"
        sent[4].lemma = "ねこ"
        sent[4].comment = "Say neh-koh"
        sent[4].pos = "名詞-一般"
        sent[6].lemma = "すき"
        sent[6].pos = "名詞-形容動詞語幹"
        c = sent.concepts.new("10084295-n", "wn", clemma="女の子", tokens=(sent[0], sent[1], sent[2]))
        sent.concept.wn.comment = "若々しい女の人"  # set comment for gold wn concept, which is c
        self.assertEqual(c.comment, "若々しい女の人")
        sent.concepts.new("02121620-n", clemma="猫").tokens.append(sent[4])
        sent.concepts.new("01292683-a", clemma="好き").tokens.append(sent[6])
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
                    'concepts': [{'value': '10084295-n', 'tokens': [0, 1, 2], 'type': 'wn', 'clemma': '女の子', 'comment': '若々しい女の人'},
                                 {'value': '02121620-n', 'tokens': [4], 'clemma': '猫'},
                                 {'value': '01292683-a', 'tokens': [6], 'clemma': '好き'}]}
        actual = sent.to_dict()
        self.assertEqual(expected['text'], actual['text'])
        self.assertEqual(expected['concepts'], actual['concepts'])
        self.assertEqual(expected['tokens'], actual['tokens'])
        self.assertEqual(expected, actual)
        getLogger().debug(actual)

    def test_json_tagged_sent(self):
        raw = {'text': '女の子は猫が好きです。',
               'tokens': [{'cfrom': 0, 'cto': 1, 'text': '女', 'lemma': 'おんな'},
                          {'cfrom': 1, 'cto': 2, 'text': 'の'},
                          {'cfrom': 2, 'cto': 3, 'text': '子', 'lemma': 'こ'},
                          {'cfrom': 3, 'cto': 4, 'text': 'は'},
                          {'cfrom': 4, 'cto': 5, 'text': '猫', 'lemma': 'ねこ', 'pos': '名詞-一般', 'comment': 'Say neh-koh'},
                          {'cfrom': 5, 'cto': 6, 'text': 'が'}, {'cfrom': 6, 'cto': 8, 'text': '好き', 'lemma': 'すき', 'pos': '名詞-形容動詞語幹'},
                          {'cfrom': 8, 'cto': 10, 'text': 'です'},
                          {'cfrom': 10, 'cto': 11, 'text': '。'}],
               'concepts': [{'clemma': '女の子', 'value': '10084295-n', 'tokens': [0, 1, 2], 'comment': '若々しい女の人', 'flag': 'G'},
                            {'clemma': '猫', 'value': '02121620-n', 'tokens': [4]},
                            {'clemma': '好き', 'value': '01292683-a', 'tokens': [6]}]}
        # json => TaggedSentence => json
        sent = ttl.Sentence.from_dict(raw)
        sent_json = sent.to_dict()
        self.assertEqual(raw['text'], sent_json['text'])
        self.assertEqual(raw['concepts'], sent_json['concepts'])
        self.assertEqual(raw['tokens'], sent_json['tokens'])
        self.assertEqual(raw, sent_json)
        self.assertEqual(sent_json['concepts'][0]['flag'], 'G')

    def test_tagging_erg_sent(self):
        """ Test import tokens """
        txt = """In this way I am no doubt indirectly responsible for Dr. Grimesby Roylott's death, and I cannot say that it is likely to weigh very heavily upon my conscience." """
        words = ['in', 'this', 'way', 'i', 'am', 'no', 'doubt', 'indirectly', 'responsible', 'for', 'dr.', 'Grimesby', 'Roylott', "'s", 'death', ',', 'and', 'i', 'can', 'not', 'say', 'that', 'it', 'is', 'likely', 'to', 'weigh', 'very', 'heavily', 'upon', 'my', 'conscience', '.', '"']
        s = ttl.Sentence(txt)
        s._import_tokens(words)
        self.assertEqual(words, [x.text for x in s.tokens])

    def test_tagged_doc(self):
        doc = ttl.read(TEST_FILE)
        ts_count = [(len(s), len(s.concepts)) for s in doc]
        self.assertEqual(len(doc), 3)  # 3 sents
        self.assertEqual(ts_count, [(29, 15), (28, 13), (34, 23)])

    def test_cwl(self):
        doc = ttl.read(TEST_FILE)
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
        doc = ttl.read(TEST_FILE)
        mw_ms = [(len(list(s.mwe())), len(list(s.msw()))) for s in doc]
        self.assertEqual(mw_ms, [(2, 2), (0, 0), (3, 2)])

    def test_recover_surface_string(self):
        s = ttl.Sentence("""a religious sect founded in the United States in 1966; based on Vedic scriptures; groups engage in joyful chanting of `Hare Krishna' and other mantras based on the name of the Hindu god Krishna; devotees usually wear saffron robes and practice vegetarianism and celibacy""")
        tokens = ['a', 'religious', 'sect', 'founded', 'in', 'the', 'United', 'States', 'in', '1966', ';', 'based', 'on', 'Vedic', 'scriptures', ';', 'groups', 'engage', 'in', 'joyful', 'chanting', 'of', 'Hare', 'Krishna', 'and', 'other', 'mantras', 'based', 'on', 'the', 'name', 'of', 'the', 'Hindu', 'god', 'Krishna', ';', 'devotees', 'usually', 'wear', 'saffron', 'robes', 'and', 'practice', 'vegetarianism', 'and', 'celibacy']
        s._import_tokens(tokens)
        cfrom = min(x.cfrom for x in s.tokens)
        cto = max(x.cto for x in s.tokens)
        self.assertEqual(s.text, s.text[cfrom:cto])

    def test_export_to_streams(self):
        doc = ttl.Document('manual', TEST_DATA)
        # create sents in doc
        raws = (sent1, sent2, sent3)
        mecab_outputs = (sent1_mecab, sent2_mecab, sent3_mecab)
        for sid, (text, mecab_output) in enumerate(zip(raws, mecab_outputs)):
            deko.mecab._mecab_output_to_sent(text, mecab_output, doc=doc)
        # sense tagging
        doc[2][4].comment = 'to eat'
        doc[0].concepts.new("三毛猫", "wiki_ja", "三毛猫", tokens=[0, 1, 2]).comment = 'Calico cat, you know?'
        doc[1].concepts.new("02756821-v", "wn", "降る", tokens=(2,))
        doc[2].concepts.new("10084295-n", "wn", "女の子", tokens=(0,))
        doc[2].concepts.new("01166351-v", "wn", "食べる", (4,))
        # tags
        doc[0].tags.new("WIKI", "src", 0, 3)
        doc[0].tags.new("https://ja.wikipedia.org/wiki/三毛猫", "url", 0, 3)
        doc[2].tags.new("WIKI","src",  0, 3)
        doc[2].tags.new("https://ja.wikipedia.org/wiki/少女", "url", 0, 3)
        # export doc
        concepts = TextReport.string()
        links = TextReport.string()
        sents = TextReport.string()
        tags = TextReport.string()
        words = TextReport.string()
        with ttl.TxtWriter(sents.file, words.file, concepts.file, links.file, tags.file) as writer:
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
            for text in doc:
                logging.debug(json.dumps(text.to_dict(), ensure_ascii=False))


class TestSerialization(unittest.TestCase):

    def build_test_sent(self):
        sent = ttl.Sentence(sent1)
        sent.flag = '0'
        sent.comment = 'written in Japanese'
        sent.tags.new('I like calico cats.', 'eng')
        sent._import_tokens('三 毛 猫 が 好き です 。'.split())
        for tk, pos in zip(sent, '名詞 名詞 名詞 助詞 名詞 助動詞 記号'.split()):
            tk.pos = pos
        sent.concepts.new("三毛猫", "wiki", "wiki.ja:三毛猫", tokens=[0, 1, 2])
        sent[0].tags.new('mi', type='reading')
        sent[1].tags.new('ke', type='reading')
        sent[2].tag.reading = 'neko'
        getLogger().debug(sent.to_dict())
        return sent

    def test_json_serialization(self):
        print("Test serialization to and from JSON")
        sent = self.build_test_sent()
        sent_dict = sent.to_dict()
        sent_re = ttl.Sentence.from_dict(sent_dict)
        getLogger().debug(sent_re.to_dict())
        self.assertEqual(sent_re.to_dict(), sent_dict)

    def test_ttl_tsv_serialization(self):
        sent = self.build_test_sent()
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
        jo = sent.to_dict()
        jr = docx[0].to_dict()
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
