# -*- coding: utf-8 -*-

# This code is a part of chirptext library: https://github.com/letuananh/chirptext
# :copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

from . import mecab
from .. import texttaglib as ttl

__JANOME_AVAILABLE = False
try:
    from janome.tokenizer import Tokenizer
    __JANOME_AVAILABLE = True
except Exception as e:
    pass


__JANOME_TOKENIZER = None


def _get_tokenizer():
    global __JANOME_TOKENIZER
    if __JANOME_TOKENIZER is None and __JANOME_AVAILABLE:
        __JANOME_TOKENIZER = Tokenizer()
    return __JANOME_TOKENIZER


def janome_available():
    ''' Check if janome package is installed '''
    return __JANOME_AVAILABLE


def _janome_parse_token_dicts(content, *args, **kwargs):
    """ Parse a sentence using janome and return a mecab-compatible list of token dicts """
    _tokenizer = _get_tokenizer()
    tokens = _tokenizer.tokenize(content)
    # format: same as mecab
    # 表層形,品詞,品詞細分類1,品詞細分類2,品詞細分類3,活用形,活用型,原形,読み,発音
    # extra[0] is pos with 4 parts
    token_dicts = []
    for token in tokens:
        if token.extra is None:
            if token.surface in ('\r', '\n', '\r\n'):
                continue
            elif token.surface == ',':
                features = (',', '記号', '読点' , '*', '*', '*', '*', ',', ',', ',')
            else:
                features = [token.surface] + [''] * 9
        else:
            features = (token.surface, *token.extra[0].split(','), *token.extra[1:])
            if len(features) < 10:
                features += [''] * (10 - len(features))
        token_dicts.append({k: v for k, v in zip(mecab._MECAB_FIELDS, features)})
    return token_dicts


def parse(text, doc=None, sent_id=None, **kwargs):
    token_dicts = _janome_parse_token_dicts(text)
    return mecab._make_sent(text, token_dicts, doc=doc, sent_id=sent_id, **kwargs)


def parse_doc(text, splitlines=True, auto_strip=True, doc_name='', **kwargs):
    """ Parse a Japanese document with multiple sentences using Mecab """
    doc = ttl.Document(name=doc_name)
    if not splitlines:
        token_dicts = _janome_parse_token_dicts(text)
        return mecab._tokenize_token_dicts(token_dicts, text, auto_strip, doc=doc)
    else:
        for line in text.splitlines():
            parse(line.strip() if auto_strip else line, doc=doc, **kwargs)
    return doc


def tokenize(text, **kwargs):
    """ Sentence to a list of tokens (string) """
    return list(Tokenizer(wakati=True).tokenize(text, wakati=True))


def tokenize_sent(content, **kwargs):
    """ Tokenize a Japanese text into sentences """
    doc = parse_doc(content, splitlines=False, **kwargs)
    return [s.text for s in doc]
