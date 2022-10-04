# -*- coding: utf-8 -*-

# This code is a part of chirptext library: https://github.com/letuananh/chirptext
# :copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import logging
from . import mecab
from .. import texttaglib as ttl

__IGO_AVAILABLE = False
__IGO_TAGGER = None


def __try_import_igo(log=False):
    global __IGO_AVAILABLE
    global __IGO_TAGGER
    try:
        from igo.Tagger import Tagger
        __IGO_TAGGER = Tagger()
        __IGO_AVAILABLE = True
    except Exception as e:
        if log:
            logging.getLogger(__name__).warning('igo-python is not installed. run `pip install igo-python` to install.', exc_info=True)
    return __IGO_AVAILABLE


def igo_available():
    ''' Check if igo-python package is installed '''
    return __IGO_AVAILABLE


__try_import_igo()


def _igo_parse_token_dicts(content, *args, **kwargs):
    """ Parse a text using igo and return a mecab-compatible list of token dicts """
    global __IGO_TAGGER
    tokens = __IGO_TAGGER.parse(content)
    # format: same as mecab
    # 表層形,品詞,品詞細分類1,品詞細分類2,品詞細分類3,活用形,活用型,原形,読み,発音
    token_dicts = []
    for token in tokens:
        features = [token.surface] + token.feature.split(',')
        if len(features) < 10:
            features += [''] * (10 - len(features))
        token_dicts.append({k: v for k, v in zip(mecab._MECAB_FIELDS, features)})
    return token_dicts


def parse(text, doc=None, sent_id=None, **kwargs):
    token_dicts = _igo_parse_token_dicts(text)
    return mecab._make_sent(text, token_dicts, doc=doc, sent_id=sent_id, **kwargs)


def parse_doc(text, splitlines=True, auto_strip=True, doc_name='', **kwargs):
    """ Parse a Japanese document with multiple sentences using Mecab """
    doc = ttl.Document(name=doc_name)
    if not splitlines:
        token_dicts = _igo_parse_token_dicts(text)
        return mecab._tokenize_token_dicts(token_dicts, text, auto_strip, doc=doc)
    else:
        for line in text.splitlines():
            parse(line.strip() if auto_strip else line, doc=doc, **kwargs)
    return doc


def tokenize(text, **kwargs):
    """ Sentence to a list of tokens (string) """
    return __IGO_TAGGER.wakati(text)


def tokenize_sent(content, **kwargs):
    """ Tokenize a Japanese text into sentences """
    doc = parse_doc(content, splitlines=False, **kwargs)
    return [s.text for s in doc]
