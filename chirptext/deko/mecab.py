# This code is a part of chirptext library: https://github.com/letuananh/chirptext
# :copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import os
import re
import logging
import platform
import subprocess
from .. import texttaglib as ttl
from . import util

# Try to use mecab-python3 if it's available
MECAB_PYTHON3 = False
MECAB_LOC = 'mecab'  # location of mecab's binary package


def __try_import_mecab(log=False):
    global MECAB_PYTHON3
    global MECAB_LOC
    MECAB_PYTHON3 = False
    try:
        import MeCab
        MeCab.Tagger().parse("Pythonが好きです。")
        MECAB_PYTHON3 = True
    except Exception:
        # use flex-mecab
        try:
            if platform.system() == 'Windows':
                if os.path.isfile("C:\\Program Files (x86)\\MeCab\\bin\\mecab.exe"):
                    MECAB_LOC = "C:\\Program Files (x86)\\MeCab\\bin\\mecab.exe"
                elif os.path.isfile("C:\\Program Files\\MeCab\\bin\\mecab.exe"):
                    MECAB_LOC = "C:\\Program Files\\MeCab\\bin\\mecab.exe"
                else:
                    MECAB_LOC = "mecab.exe"
            elif os.path.isfile('/usr/local/bin/mecab'):
                MECAB_LOC = '/usr/local/bin/mecab'
            else:
                MECAB_LOC = "mecab"
        except Exception:
            pass
        if log:
            logging.getLogger(__name__).warning("mecab-python3 could not be loaded. mecab binary package will be used ({})".format(MECAB_LOC))
    return MECAB_PYTHON3


__try_import_mecab()


def _register_mecab_loc(location):
    ''' Set MeCab binary location '''
    global MECAB_LOC
    if not os.path.isfile(location):
        logging.getLogger(__name__).warning("Provided mecab binary location does not exist ({})".format(location))
    logging.getLogger(__name__).info("Mecab binary is switched to: {}".format(location))
    MECAB_LOC = location


def _get_mecab_loc():
    ''' Get MeCab binary location '''
    return MECAB_LOC


def run_mecab_process(content, *args, **kwargs):
    ''' Use subprocess to run mecab '''
    encoding = 'utf-8' if 'encoding' not in kwargs else kwargs['encoding']
    mecab_loc = kwargs['mecab_loc'] if 'mecab_loc' in kwargs else None
    if mecab_loc is None:
        mecab_loc = MECAB_LOC
    proc_args = [mecab_loc]
    if args:
        proc_args.extend(args)
    output = subprocess.run(proc_args,
                            input=content.encode(encoding),
                            stdout=subprocess.PIPE)
    output_string = os.linesep.join(output.stdout.decode(encoding).splitlines())
    return output_string


def _internal_mecab_parse(content, *args, **kwargs):
    ''' Use mecab-python3 by default to parse JP text. Fall back to mecab binary app if needed '''
    global MECAB_PYTHON3
    if 'mecab_loc' not in kwargs and MECAB_PYTHON3 and 'MeCab' in globals():
        return MeCab.Tagger(*args).parse(content)
    else:
        return run_mecab_process(content, *args, **kwargs)


def wakati(content):
    return _internal_mecab_parse(content, '-Owakati')


def version():
    output = run_mecab_process("", "--version")
    if output:
        return output.strip()
    else:
        return None


# -----------------------------------------------------------------------------
# Mecab-TTL functions
# -----------------------------------------------------------------------------

MECAB_EOS_TOKEN = {'surface': 'EOS', 'pos': '', 'sc1': '', 'sc2': '', 'sc3': '', 'inf': '',
                   'conj': '', 'root': '', 'reading': '', 'pron': ''}


def _is_eos(token):
    return token == MECAB_EOS_TOKEN


_MECAB_FIELDS = ['surface', 'pos', 'sc1', 'sc2', 'sc3', 'inf', 'conj', 'root', 'reading', 'pron']


def _token_pos3(token):
    """ Use pos-sc1-sc2 as POS """
    parts = [token.pos]
    if token.sc1 and token.sc1 != '*':
        parts.append(token.tag.sc1.value)
        if token.sc2 and token.sc2 != '*':
            parts.append(token.tag.sc2.value)
    return '-'.join(x for x in parts)


# Reference: http://taku910.github.io/mecab/#parse
# MeCabToken = namedtuple('MeCabToken', 'surface pos sc1 sc2 sc3 inf conj root reading pron'.split())
def _mecab_line_to_token_dicts(raw):
    parts = re.split('\t|,', raw)
    if len(parts) < 10:
        parts += [''] * (10 - len(parts))
    # (surface, pos, sc1, sc2, sc3, inf, conj, root, reading, pron) = parts
    return {k: v for k, v in zip(_MECAB_FIELDS, parts)}


def _make_sent(text, token_dicts, doc: ttl.Document = None, sent_id=None):
    if doc is None:
        sent = ttl.Sentence(text, ID=sent_id)
    else:
        sent = doc.sents.new(text, ID=sent_id)
    # import tokens
    sent.tokens = (token['surface'] for token in token_dicts if not _is_eos(token))
    for token, token_dict in zip(sent, token_dicts):
        for k in ['sc1', 'sc2', 'sc3', 'inf', 'conj']:
            if token_dict[k] and token_dict[k] != '*':
                token[k] = token_dict[k]
        token.pos = token_dict['pos']
        token.tag.pos3 = _token_pos3(token)
        # root is mapped to lemma
        if "root" in token_dict and token_dict["root"] and token_dict["root"] != "*":
            token.lemma = token_dict["root"]
        if "reading" in token_dict:
            token.reading = token_dict['reading']
            token.tag.reading_hira = util.kata2hira(token_dict['reading'])
        if "pron" in token_dict:
            token.pron = token_dict['pron']
    return sent


def _mecab_output_to_sent(text, mecab_output, doc: ttl.Document = None, sent_id=None):
    """ Parse mecab output

    :param text: Original text that was fed into mecab
    :param mecab_output: text retrieved from mecab output stream
    """
    lines = mecab_output.splitlines()
    token_dicts = [_mecab_line_to_token_dicts(x) for x in lines]
    return _make_sent(text, token_dicts, doc=doc, sent_id=sent_id)


def _tokenize_token_dicts(token_dicts, raw='', auto_strip=True, doc=None):
    """ Tokenize a text to multiple sentences """
    doc = doc if doc else ttl.Document()
    bucket = []
    cfrom = 0
    cto = 0
    logging.getLogger(__name__).debug("raw text: {}".format(raw))
    logging.getLogger(__name__).debug("tokens: {}".format(token_dicts))
    for token_dict in token_dicts:
        if _is_eos(token_dict):
            continue
        token_cfrom = raw.find(token_dict['surface'], cto)
        cto = token_cfrom + len(token_dict['surface'])  # also token_cto
        bucket.append(token_dict)
        # sentence ending
        if token_dict['pos'] == '記号' and token_dict['sc1'] == '句点':
            current_text = raw[cfrom:cto].strip() if auto_strip else raw[cfrom:cto]
            _make_sent(current_text, bucket, doc=doc)
            cfrom = cto
            bucket = []
    if bucket:
        logging.getLogger(__name__).debug("Bucket is not empty: {}".format(bucket))
        last_sent_text = raw[cfrom:cto]
        logging.getLogger(__name__).debug("remaining text: {} [{}:{}]".format(last_sent_text, cfrom, cto))
        if auto_strip:
            last_sent_text = last_sent_text.strip()
        _make_sent(last_sent_text, bucket, doc=doc)
    return doc


def parse(text, doc=None, **kwargs):
    """ Use mecab to parse one sentence """
    mecab_output = _internal_mecab_parse(text, **kwargs)
    return _mecab_output_to_sent(text, mecab_output, doc=doc)


def parse_doc(text, splitlines=True, auto_strip=True, doc_name='', **kwargs):
    """ Parse a Japanese document with multiple sentences using Mecab """
    doc = ttl.Document(name=doc_name)
    if not splitlines:
        lines = _internal_mecab_parse(text, **kwargs).splitlines()
        token_dicts = [_mecab_line_to_token_dicts(line) for line in lines]
        return _tokenize_token_dicts(token_dicts, text, auto_strip, doc=doc)
    else:
        for line in text.splitlines():
            parse(line.strip() if auto_strip else line, doc=doc, **kwargs)
    return doc


def tokenize(content, use_wakati=True, **kwargs):
    """ Sentence to a list of tokens (string) """
    if use_wakati:
        return [x for x in wakati(content).split(' ') if x]
    else:
        return [x.text for x in parse(content, **kwargs)]


def tokenize_sent(content, **kwargs):
    """ Tokenize a Japanese text into sentences """
    doc = parse_doc(content, splitlines=False, **kwargs)
    return [s.text for s in doc]
