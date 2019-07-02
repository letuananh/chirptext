# -*- coding: utf-8 -*-

'''
Functions for processing Japanese text

Latest version can be found at https://github.com/letuananh/chirptext

References:
    MeCab homepage:
        http://taku910.github.io/mecab/

MeCab, デコ, got the joke?
* This script was a part of omwtk

:copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
:license: MIT, see LICENSE for more details.
'''

import re
import os
import logging
import warnings

from . import texttaglib as ttl
from .dekomecab import wakati, parse as _internal_mecab_parse, _register_mecab_loc as set_mecab_bin, _get_mecab_loc as get_mecab_bin


# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

DATA_FOLDER = os.path.abspath(os.path.expanduser('./data'))

# reference: https://en.wikipedia.org/wiki/Hiragana_%28Unicode_block%29
# U+304x 		ぁ 	あ 	ぃ 	い 	ぅ 	う 	ぇ 	え 	ぉ 	お 	か 	が 	き 	ぎ 	く
# U+305x 	ぐ 	け 	げ 	こ 	ご 	さ 	ざ 	し 	じ 	す 	ず 	せ 	ぜ 	そ 	ぞ 	た
# U+306x 	だ 	ち 	ぢ 	っ 	つ 	づ 	て 	で 	と 	ど 	な 	に 	ぬ 	ね 	の 	は
# U+307x 	ば 	ぱ 	ひ 	び 	ぴ 	ふ 	ぶ 	ぷ 	へ 	べ 	ぺ 	ほ 	ぼ 	ぽ 	ま 	み
# U+308x 	む 	め 	も 	ゃ 	や 	ゅ 	ゆ 	ょ 	よ 	ら 	り 	る 	れ 	ろ 	ゎ 	わ
# U+309x 	ゐ 	ゑ 	を 	ん 	ゔ 	ゕ 	ゖ 			゙ 	゚ 	゛ 	゜ 	ゝ 	ゞ 	ゟ

HIRAGANA = 'ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんゔゕゖ゙゚゛゜ゝゞゟ'

# reference: https://en.wikipedia.org/wiki/Katakana_%28Unicode_block%29
# U+30Ax 	゠ 	ァ 	ア 	ィ 	イ 	ゥ 	ウ 	ェ 	エ 	ォ 	オ 	カ 	ガ 	キ 	ギ 	ク
# U+30Bx 	グ 	ケ 	ゲ 	コ 	ゴ 	サ 	ザ 	シ 	ジ 	ス 	ズ 	セ 	ゼ 	ソ 	ゾ 	タ
# U+30Cx 	ダ 	チ 	ヂ 	ッ 	ツ 	ヅ 	テ 	デ 	ト 	ド 	ナ 	ニ 	ヌ 	ネ 	ノ 	ハ
# U+30Dx 	バ 	パ 	ヒ 	ビ 	ピ 	フ 	ブ 	プ 	ヘ 	ベ 	ペ 	ホ 	ボ 	ポ 	マ 	ミ
# U+30Ex 	ム 	メ 	モ 	ャ 	ヤ 	ュ 	ユ 	ョ 	ヨ 	ラ 	リ 	ル 	レ 	ロ 	ヮ 	ワ
# U+30Fx 	ヰ 	ヱ 	ヲ 	ン 	ヴ 	ヵ 	ヶ 	ヷ 	ヸ 	ヹ 	ヺ 	・ 	ー 	ヽ 	ヾ 	ヿ
KATAKANA = '゠ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶヷヸヹヺ・ーヽヾヿ'
KATA2HIRA_TRANS = str.maketrans(KATAKANA[1:87], HIRAGANA[:86])


def getLogger():
    return logging.getLogger(__name__)


def simple_kata2hira(input_str):
    return input_str.translate(KATA2HIRA_TRANS)


def is_kana(text):
    ''' Check if a text if written in kana only (hiragana & katakana)
    if text is empty then return True
    '''
    if text is None:
        raise ValueError("text cannot be None")
    for c in text:
        if c not in HIRAGANA and c not in KATAKANA:
            return False
    return True


try:
    from jaconv import kata2hira
except:
    # if jaconv is not available, use built-in method
    kata2hira = simple_kata2hira


# -------------------------------------------------------------------------------
# Data Structures
# -------------------------------------------------------------------------------

# Reference: http://taku910.github.io/mecab/#parse
# MeCabToken = namedtuple('MeCabToken', 'surface pos sc1 sc2 sc3 inf conj root reading pron'.split())
class MeCabToken(object):
    def __init__(self, surface, pos=None, sc1=None, sc2=None, sc3=None, inf=None, conj=None, root=None, reading=None, pron=None):
        self.surface = surface
        self.pos = pos
        self.sc1 = sc1
        self.sc2 = sc2
        self.sc3 = sc3
        self.inf = inf
        self.conj = conj
        self.root = root
        self.reading = reading
        self.pron = pron
        self.is_eos = (surface == 'EOS' and pos == sc1 == sc2 == sc3 == inf == conj == root == reading == pron == '')

    def __str__(self):
        return '[{sur}({pos}-{s1}/{s2}/{s3}|{ro}|{re}|{pr})]'.format(sur=self.surface, pos=self.pos, s1=self.sc1, s2=self.sc2, s3=self.sc3, ro=self.root, re=self.reading, pr=self.pron)

    def __repr__(self):
        return str(self)

    def reading_hira(self):
        return kata2hira(self.reading)

    def need_ruby(self):
        return self.reading and self.reading != self.surface and self.reading_hira() != self.surface

    def pos3(self):
        ''' Use pos-sc1-sc2 as POS '''
        parts = [self.pos]
        if self.sc1 and self.sc1 != '*':
            parts.append(self.sc1)
            if self.sc2 and self.sc2 != '*':
                parts.append(self.sc2)
        return '-'.join(parts)

    def to_ruby(self):
        ''' Convert one MeCabToken into HTML '''
        if self.need_ruby():
            surface = self.surface
            reading = self.reading_hira()
            return '<ruby><rb>{sur}</rb><rt>{read}</rt></ruby>'.format(sur=surface, read=reading)
        elif self.is_eos:
            return ''
        else:
            return self.surface

    @staticmethod
    def parse(raw):
        parts = re.split('\t|,', raw)
        if len(parts) < 10:
            parts += [''] * (10 - len(parts))
        (surface, pos, sc1, sc2, sc3, inf, conj, root, reading, pron) = parts
        return MeCabToken(surface, pos, sc1, sc2, sc3, inf, conj, root, reading, pron)

    def to_csv(self):
        return '{sur}\t{pos}\t{s1}\t{s2}\t{s3}\t{inf}\t{conj}\t{ro}\t{re}\t{pr}'.format(sur=self.surface, pos=self.pos, s1=self.sc1, s2=self.sc2, s3=self.sc3, inf=self.inf, conj=self.conj, ro=self.root, re=self.reading, pr=self.pron)


class MeCabSent(object):

    def __init__(self, surface, tokens):
        self.surface = surface
        self.tokens = []
        if tokens:
            self.tokens.extend(tokens)

    def to_ruby(self):
        s = []
        for x in self.tokens:
            s.append(x.to_ruby())
        stext = ' '.join(s)
        # clean sentence a bit ...
        stext = stext.replace(' 。', '。').replace('「 ', '「').replace(' 」', '」').replace(' 、 ', '、').replace('（ ', '（').replace(' ）', '）')
        return stext

    def __getitem__(self, value):
        return self.tokens[value]

    def __len__(self):
        return len(self.tokens)

    @property
    def words(self):
        return [x.surface for x in self.tokens if not x.is_eos]

    @property
    def text(self):
        return self.surface if self.surface else str(self)

    def __repr__(self):
        return "MeCabSent({})".format(repr(self.text))

    def __str__(self):
        return ' '.join([x.surface for x in self.tokens if not x.is_eos])

    def to_ttl(self):
        tsent = ttl.Sentence(self.surface)
        tsent.import_tokens(self.words)
        for mtk, tk in zip((tk for tk in self if not tk.is_eos), tsent):
            tk.pos = mtk.pos3()
            if mtk.root and mtk.root != '*':
                tk.lemma = mtk.root
            else:
                tk.lemma = mtk.surface
            tk.new_tag(mtk.reading_hira(), tagtype="reading", source=ttl.Tag.MECAB)
        return tsent

    @staticmethod
    def parse(text, **kwargs):
        ''' Use mecab to parse one sentence '''
        mecab_out = _internal_mecab_parse(text, **kwargs).splitlines()
        tokens = [MeCabToken.parse(x) for x in mecab_out]
        return MeCabSent(text, tokens)


class DekoText(object):

    def __init__(self, name=''):
        self.sents = []
        self.name = name

    def __len__(self):
        return len(self.sents)

    def __getitem__(self, name):
        return self.sents[name]

    def add(self, sentence_text, **kwargs):
        ''' Parse a text string and add it to this doc '''
        sent = MeCabSent.parse(sentence_text, **kwargs)
        self.sents.append(sent)
        return sent

    def __str__(self):
        return "\n".join(["#{}. {}".format(idx + 1, x) for idx, x in enumerate(self)])

    def to_ttl(self, name=None):
        doc = ttl.Document(name=name if name else self.name)
        for sent in self.sents:
            doc.add_sent(sent.to_ttl())
        return doc

    @staticmethod
    def parse(text, splitlines=True, auto_strip=True, **kwargs):
        doc = DekoText()
        if not splitlines:
            # surface is broken right now ...
            tokens = MeCabSent.parse(text, **kwargs)
            doc.sents = tokenize_sent(tokens, text, auto_strip)
        else:
            lines = text.splitlines()
            for line in lines:
                if auto_strip:
                    doc.add(line.strip(), **kwargs)  # auto-parse
                else:
                    doc.add(line, **kwargs)  # auto-parse
        return doc


# -------------------------------------------------------------------------------
# MeCab helper functions
# -------------------------------------------------------------------------------

def _lines2mecab(lines, **kwargs):
    ''' Use mecab to parse many lines '''
    sents = []
    for line in lines:
        sent = MeCabSent.parse(line, **kwargs)
        sents.append(sent)
    return sents


# -------------------------------------------------------------------------------
# Legacy functions
# -------------------------------------------------------------------------------

def txt2mecab(text, **kwargs):
    warnings.warn("txt2mecab() is deprecated and will be removed in near future. Use deko.parse() instead.", DeprecationWarning, stacklevel=2)
    return MeCabSent.parse(text, **kwargs)


def lines2mecab(lines, **kwargs):
    warnings.warn("lines2mecab() is deprecated and will be removed in near future.", DeprecationWarning, stacklevel=2)
    return _lines2mecab(lines, **kwargs)


# -------------------------------------------------------------------------------
# Functions
# -------------------------------------------------------------------------------

def tokenize(content, **kwargs):
    ''' Sentence to a list of tokens (string) '''
    # TODO: Check if wakati better?
    # return wakati(content).split(' ')
    return MeCabSent.parse(content, **kwargs).words


# TODO: Need to calculate cfrom, cto to get surfaces
def tokenize_sent(mtokens, raw='', auto_strip=True):
    ''' Tokenize a text to multiple sentences '''
    sents = []
    bucket = []
    cfrom = 0
    cto = 0
    token_cfrom = 0
    logger = getLogger()
    logger.debug("raw text: {}".format(raw))
    logger.debug("tokens: {}".format(mtokens))
    for t in mtokens:
        if t.is_eos:
            continue
        token_cfrom = raw.find(t.surface, cto)
        cto = token_cfrom + len(t.surface)  # also token_cto
        logger.debug("processing token {} <{}:{}>".format(t, token_cfrom, cto))
        bucket.append(t)
        # sentence ending
        if t.pos == '記号' and t.sc1 == '句点':
            sent_text = raw[cfrom:cto]
            getLogger().debug("sent_text = {} | <{}:{}>".format(sent_text, cfrom, cto))
            if auto_strip:
                sent_text = sent_text.strip()
            sents.append(MeCabSent(sent_text, bucket))
            logger.debug("Found a sentence: {}".format(sent_text))
            cfrom = cto
            bucket = []
    if bucket:
        logger.debug("Bucket is not empty: {}".format(bucket))
        sent_text = raw[cfrom:cto]
        logger.debug("remaining text: {} [{}:{}]".format(sent_text, cfrom, cto))
        if auto_strip:
            sent_text = sent_text.strip()
        sents.append(MeCabSent(sent_text, bucket))
    return sents


def analyse(content, splitlines=True, format=None, **kwargs):
    ''' Japanese text > tokenize/txt/html '''
    sents = DekoText.parse(content, splitlines=splitlines, **kwargs)
    doc = []
    final = sents
    # Generate output
    if format == 'html':
        for sent in sents:
            doc.append(sent.to_ruby())
        final = '<br/>\n'.join(doc)
    elif format == 'csv':
        for sent in sents:
            doc.append('\n'.join([x.to_csv() for x in sent]) + '\n')
        final = '\n'.join(doc)
    elif format == 'txt':
        final = '\n'.join([str(x) for x in sents])
    return final


# useful alias
parse = MeCabSent.parse
parse_doc = DekoText.parse
