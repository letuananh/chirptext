# -*- coding: utf-8 -*-

'''
Functions for processing Japanese text

Latest version can be found at https://github.com/letuananh/chirptext

References:
    MeCab homepage:
        http://taku910.github.io/mecab/

MeCab, デコ, got the joke?
* This script is used to be a part of omwtk

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

import re
import os
import logging

import MeCab
import jaconv


# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

def getLogger():
    return logging.getLogger(__name__)


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
        return jaconv.kata2hira(self.reading)

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

    mecab = MeCab.Tagger()

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

    def __str__(self):
        return ' '.join([x.surface for x in self.tokens if not x.is_eos])

    @staticmethod
    def parse(text):
        ''' Use mecab to parse one sentence '''
        mecab_out = MeCabSent.mecab.parse(text).splitlines()
        tokens = [MeCabToken.parse(x) for x in mecab_out]
        return MeCabSent(text, tokens)


class DekoText(object):

    def __init__(self):
        self.sents = []

    def __len__(self):
        return len(self.sents)

    def __getitem__(self, name):
        return self.sents[name]

    def add(self, sentence_text):
        ''' Parse a text string and add it to this doc '''
        sent = MeCabSent.parse(sentence_text)
        self.sents.append(sent)
        return sent

    def __str__(self):
        return "\n".join(["#{}. {}".format(idx + 1, x) for idx, x in enumerate(self)])

    @staticmethod
    def parse(text, splitlines=True, auto_strip=True):
        doc = DekoText()
        if not splitlines:
            # surface is broken right now ...
            tokens = txt2mecab(text)
            doc.sents = tokenize_sent(tokens, text, auto_strip)
        else:
            lines = text.splitlines()
            for line in lines:
                if auto_strip:
                    doc.add(line.strip())
                else:
                    doc.add(line)
        return doc


# -------------------------------------------------------------------------------
# Functions
# -------------------------------------------------------------------------------

def txt2mecab(text):
    ''' Use mecab to parse one sentence '''
    mecab = MeCab.Tagger()
    mecab_out = mecab.parse(text).splitlines()
    tokens = [MeCabToken.parse(x) for x in mecab_out]
    return MeCabSent(text, tokens)


def lines2mecab(lines):
    ''' Use mecab to parse many lines '''
    sents = []
    for line in lines:
        sent = txt2mecab(line)
        sents.append(sent)
    return sents


# TODO: Need to calculate cfrom, cto to get surfaces
def tokenize_sent(mtokens, raw='', auto_strip=True):
    sents = []
    bucket = []
    cfrom = 0
    cto = 0
    token_cfrom = 0
    for t in mtokens:
        if t.is_eos:
            break
        token_cfrom = raw.find(t.surface, cto)
        cto = token_cfrom + len(t.surface)
        if not t.is_eos:
            bucket.append(t)
        if t.pos == '記号' and t.sc1 == '句点':
            sent_text = raw[cfrom:cto]
            if auto_strip:
                sent_text = sent_text.strip()
            sents.append(MeCabSent(sent_text, bucket))
            cfrom = cto
            bucket = []
    if bucket:
        sent_text = raw[cfrom:cto]
        if auto_strip:
            sent_text = sent_text.strip()
        sents.append(MeCabSent(sent_text, bucket))
    return sents


def wakati(content):
    return MeCab.Tagger("-O wakati").parse(content)


def tokenize(content):
    ''' Sentence to a list of tokens (string) '''
    # TODO: Check if wakati better?
    # return wakati(content).split(' ')
    return txt2mecab(content).words


def analyse(content, splitlines=True, format=None):
    ''' Japanese text > tokenize/txt/html '''
    sents = DekoText.parse(content, splitlines=splitlines)
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
