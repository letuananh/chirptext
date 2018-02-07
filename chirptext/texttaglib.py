# -*- coding: utf-8 -*-

''' Text Annotation library

Latest version can be found at https://github.com/letuananh/chirptext

@author: Le Tuan Anh <tuananh.ke@gmail.com>
@license: MIT
'''

# Copyright (c) 2014, Le Tuan Anh <tuananh.ke@gmail.com>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

########################################################################

import os
import logging
import json
import csv
from collections import namedtuple
from collections import defaultdict as dd
from collections import OrderedDict

from chirptext import FileHelper, FileHub
from chirptext.io import CSV


# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

STD_DIALECT = 'excel-tab'
STD_QUOTING = csv.QUOTE_MINIMAL
TokenInfo = namedtuple("TokenInfo", ['text', 'sk'])


def getLogger():
    return logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------

class Tag(object):

    DEFAULT = 'n/a'
    GOLD = 'gold'
    ISF = 'isf'
    LELESK = 'lelesk'
    NTUMC = 'ntumc'
    MFS = 'mfs'
    MECAB = 'mecab'
    NLTK = 'nltk'
    WORDNET = 'wn'
    BABELNET = 'bn'
    OTHER = 'other'

    def __init__(self, label, cfrom=-1, cto=-1, tagtype='', source=DEFAULT):
        self.cfrom = cfrom
        self.cto = cto
        self.label = label
        self.source = source
        self.tagtype = tagtype  # tag type

    def __repr__(self):
        if not self.tagtype:
            return '`{}`'.format(self.label)
        else:
            return '`{}:{}`'.format(self.tagtype, self.label)

    def __str__(self):
        return "`{l}`<{f}:{t}>{v}".format(l=self.label, f=self.cfrom, t=self.cto, v=self.tagtype)

    def to_json(self):
        a_dict = {'label': self.label}
        if self.tagtype:
            a_dict['type'] = self.tagtype
        if self.source:
            a_dict['source'] = self.source
        if self.cfrom >= 0 and self.cto >= 0:
            a_dict['cfrom'] = self.cfrom
            a_dict['cto'] = self.cto
        return a_dict


class Sentence(object):

    def __init__(self, text, ID=None, tags=None, tokens=None):
        self.text = text
        self.ID = ID
        self.__tags = []
        if tags:
            self.__tags.extend(tags)
        self.__tokens = []
        if tokens:
            self.__tokens.extend(tokens)
        self.__concepts = []
        self.__concept_map = OrderedDict()  # concept.ID to concept object

    def __str__(self):
        # return format_tag(self)
        if self.ID:
            return "#{id}: {txt}".format(id=self.ID, txt=self.text)
        else:
            return self.text

    def __getitem__(self, idx):
        return self.__tokens[idx]

    def __len__(self):
        return len(self.__tokens)

    @property
    def tags(self):
        ''' Sentence level tags '''
        return self.__tags

    @property
    def tokens(self):
        return self.__tokens

    @property
    def concepts(self):
        return self.__concepts

    def tcmap(self):
        ''' Create a tokens-concepts map '''
        tcmap = dd(list)
        for concept in self.__concept_map.values():
            for w in concept.tokens:
                tcmap[w].append(concept)
        return tcmap

    def mwe(self):
        ''' Return a generator of concepts that are linked to more than 1 token. '''
        return (c for c in self.__concepts if len(c.tokens) > 1)

    def msw(self):
        ''' Return a generator of tokens with more than one sense. '''
        return (t for t, c in self.tcmap().items() if len(c) > 1)

    def surface(self, tag):
        ''' Get surface string that is associated with a tag object '''
        if tag.cfrom >= 0 and tag.cto >= 0:
            return self.text[tag.cfrom:tag.cto]
        else:
            return ''

    def new_tag(self, label, cfrom=-1, cto=-1, tagtype='', **kwargs):
        ''' Create a sentence-level tag '''
        tag_obj = Tag(label, cfrom, cto, tagtype=tagtype, **kwargs)
        self.tags.append(tag_obj)
        return tag_obj

    def new_token(self, text, cfrom=-1, cto=-1, *args, **kwargs):
        tk = Token(text, cfrom, cto, sent=self, *args, **kwargs)
        self.__tokens.append(tk)
        return tk

    def new_concept_id(self):
        ID = 0
        while ID in self.__concept_map:
            ID += 1
        return ID

    def new_concept(self, tag, clemma="", tokens=None, ID=None, **kwargs):
        ''' Create a new concept object and add it to concept list
        tokens can be a list of Token objects or token indices
        '''
        if ID is None:
            ID = self.new_concept_id()
        if tokens:
            tokens = (t if isinstance(t, Token) else self[t] for t in tokens)
        c = Concept(ID, tag, clemma=clemma, sent=self, tokens=tokens, **kwargs)
        return self.add_concept(c)

    def add_concept(self, concept_obj):
        ''' Add a concept to current concept list '''
        if concept_obj is None:
            raise Exception("Concept object cannot be None")
        elif concept_obj in self.__concepts:
            raise Exception("Concept object is already inside")
        elif concept_obj.ID in self.__concept_map:
            raise Exception("Duplicated concept ID ({})".format(concept_obj.ID))
        self.__concepts.append(concept_obj)
        self.__concept_map[concept_obj.ID] = concept_obj
        return concept_obj

    def pop_concept(self, cid, **kwargs):
        if cid not in self.__concept_map:
            if 'default' in kwargs:
                return kwargs['default']
            else:
                raise KeyError("Invalid cid")
        concept_obj = self.concept(cid)
        self.__concept_map.pop(cid)
        self.__concepts.remove(concept_obj)
        return concept_obj

    def concept(self, cid):
        ''' Get concept by concept ID '''
        return self.__concept_map[cid]

    def to_json(self):
        sent_dict = {'text': self.text,
                     'tokens': [t.to_json() for t in self.tokens],
                     'concepts': [c.to_json() for c in self.concepts]}
        if self.ID is not None:
            sent_dict['ID'] = self.ID
        return sent_dict

    def import_tokens(self, tokens, import_hook=None, ignorecase=True):
        ''' Import a list of string as tokens '''
        text = self.text.lower() if ignorecase else self.text
        has_hooker = import_hook and callable(import_hook)
        cfrom = 0
        for token in tokens:
            if has_hooker:
                import_hook(token)
            start = text.find(token.lower() if ignorecase else token, cfrom)
            if start == -1:
                raise LookupError('Cannot find token `{t}` in sent `{s}`({l}) from {i} ({p})'.format(t=token, s=self.text, l=len(self.text), i=cfrom, p=self.text[cfrom:cfrom + 20]))
            cfrom = start
            cto = cfrom + len(token)
            self.new_token(token, cfrom, cto)
            cfrom = cto - 1

    def fix_cfrom_cto(self, import_hook=None, ignorecase=True):
        text = self.text.lower() if ignorecase else self.text
        has_hooker = import_hook and callable(import_hook)
        cfrom = 0
        for token in self.tokens:
            if has_hooker:
                import_hook(token.text)
            start = text.find(token.text.lower() if ignorecase else token.text, cfrom)
            if start == -1:
                raise LookupError('Cannot find token `{t}` in sent `{s}`({l}) from {i} ({p})'.format(t=token, s=self.text, l=len(self.text), i=cfrom, p=self.text[cfrom:cfrom + 20]))
            cfrom = start
            cto = cfrom + len(token.text)
            token.cfrom = cfrom
            token.cto = cto
            cfrom = cto - 1

    @staticmethod
    def from_json(json_sent):
        sent = Sentence(json_sent['text'])
        if 'ID' in json_sent:
            sent.ID = json_sent['ID']
        for json_token in json_sent['tokens']:
            token = sent.new_token(json_token['text'], json_token['cfrom'], json_token['cto'])
            if 'pos' in json_token:
                token.pos = json_token['pos']
            if 'lemma' in json_token:
                token.lemma = json_token['lemma']
            if 'comment' in json_token:
                token.comment = json_token['comment']
        # import concepts
        for json_concept in json_sent['concepts']:
            clemma = json_concept['clemma']
            tag = json_concept['tag']
            tokenids = json_concept['tokens']
            tokens = [sent[tid] for tid in tokenids]
            concept = sent.new_concept(tag, clemma=clemma, tokens=tokens)
            if Concept.COMMENT in json_concept:
                concept.comment = json_concept[Concept.COMMENT]
            if Concept.FLAG in json_concept:
                concept.flag = json_concept[Concept.FLAG]

        return sent


class Token(object):

    def __init__(self, text, cfrom, cto, sent=None, pos=None, lemma=None, comment=None, source=Tag.DEFAULT):
        ''' A token (e.g. a word in a sentence) '''
        self.cfrom = cfrom
        self.cto = cto
        self.__tags = []
        self.sent = sent
        self.text = text
        self.lemma = lemma
        self.pos = pos
        self.comment = comment

    def __getitem__(self, idx):
        return self.__tags[idx]

    def __len__(self):
        return len(self.__tags)

    def __iter__(self):
        return iter(self.__tags)

    def surface(self):
        if self.sent and self.sent.text:
            return self.sent.text[self.cfrom:self.cto]
        elif self.text:
            return self.text
        else:
            return ''

    def __repr__(self):
        return "`{l}`<{f}:{t}>".format(l=self.text, f=self.cfrom, t=self.cto)

    def tag_map(self):
        ''' Build a map from tagtype to list of tags '''
        tm = dd(list)
        for tag in self.__tags:
            tm[tag.tagtype].append(tag)
        return tm

    def __str__(self):
        return "`{l}`<{f}:{t}>{tgs}".format(l=self.text, f=self.cfrom, t=self.cto, tgs=self.__tags if self.__tags else '')

    def new_tag(self, label, cfrom=None, cto=None, tagtype=None, source=Tag.DEFAULT):
        ''' Create a new tag on this token '''
        if not cfrom:
            cfrom = self.cfrom
        if not cto:
            cto = self.cto
        tag = Tag(label=label, cfrom=cfrom, cto=cto, tagtype=tagtype)
        self.__tags.append(tag)
        return tag

    def to_json(self):
        token_json = {'cfrom': self.cfrom,
                      'cto': self.cto,
                      'text': self.text}
        if self.lemma:
            token_json['lemma'] = self.lemma
        if self.pos:
            token_json['pos'] = self.pos
        if self.comment:
            token_json['comment'] = self.comment
        tagdict = {k if k else 'unsorted': [t.label for t in tags] for k, tags in self.tag_map().items()}
        if tagdict:
            token_json['tags'] = tagdict
        return token_json


class Concept(object):

    FLAG = 'flag'
    COMMENT = 'comment'
    NOT_MATCHED = 'E'

    def __init__(self, ID, tag, clemma, sent=None, tokens=None, comment=None):
        self.ID = ID
        self.clemma = clemma
        self.tag = tag
        self.sent = sent
        self.comment = ''
        self.__tokens = []
        if tokens:
            self.__tokens.extend(tokens)
        self.flag = None

    @property
    def tokens(self):
        return self.__tokens

    def add_token(self, *tokens):
        for token in tokens:
            self.__tokens.append(token)

    def __repr__(self):
        return '<{t}:"{l}">'.format(l=self.clemma, t=self.tag)

    def __str__(self):
        return '<{t}:"{l}">({ws})'.format(l=self.clemma, t=self.tag, ws=self.__tokens)

    def to_json(self):
        if self.sent:
            # get token idx from sent
            tokens = [self.sent.tokens.index(t) for t in self.__tokens]
        else:
            tokens = [t.text for t in self.__tokens]
        cdict = {
            'clemma': self.clemma,
            'tag': self.tag,
            'tokens': tokens
        }
        if self.comment:
            cdict[Concept.COMMENT] = self.comment
        if self.flag:
            cdict[Concept.FLAG] = self.flag
        return cdict


class Document(object):

    def __init__(self, name, path='.'):
        self.__path = FileHelper.abspath(path)
        self.__name = name
        self.__sents = []
        self.__sent_map = {}

    @property
    def name(self):
        return self.__name

    @property
    def path(self):
        return self.__path

    def __len__(self):
        return len(self.__sents)

    def __getitem__(self, idx):
        return self.__sents[idx]

    def get(self, sent_id):
        if sent_id is None or not self.has_id(sent_id):
            raise Exception("Invalid sentence ID")
        return self.__sent_map[sent_id]

    @property
    def sent_path(self):
        return os.path.join(self.path, '{}_sents.txt'.format(self.name))

    @property
    def token_path(self):
        return os.path.join(self.path, '{}_tokens.txt'.format(self.name))

    @property
    def concept_path(self):
        return os.path.join(self.path, '{}_concepts.txt'.format(self.name))

    @property
    def link_path(self):
        return os.path.join(self.path, '{}_links.txt'.format(self.name))

    @property
    def tag_path(self):
        return os.path.join(self.path, '{}_tags.txt'.format(self.name))

    def has_id(self, sent_id):
        return sent_id in self.__sent_map

    def add_sent(self, sent_obj):
        ''' Add a ttl.Sentence object to this document '''
        if sent_obj is None:
            raise Exception("Sentence object cannot be None")
        elif sent_obj.ID is None:
            raise Exception("Sentence ID cannot be None")
        elif self.has_id(sent_obj.ID):
            raise Exception("Sentence ID {} exists".format(sent_obj.ID))
        self.__sent_map[sent_obj.ID] = sent_obj
        self.__sents.append(sent_obj)
        return sent_obj

    def new_sent(self, text, ID):
        ''' Create a new sentence and add it to this Document '''
        return self.add_sent(Sentence(text, ID=ID))

    def pop(self, sent_id, **kwargs):
        ''' If sent_id exists, remove and return the associated sentence object else return default.
        If no default is provided, KeyError will be raised.'''
        if not self.has_id(sent_id):
            if 'default' in kwargs:
                return kwargs['default']
            else:
                raise KeyError("Sentence ID {} does not exist".format(sent_id))
        else:
            # sentence exists ...
            sent_obj = self.get(sent_id)
            self.__sent_map.pop(sent_id)
            self.__sents.remove(sent_obj)
            return sent_obj

    def read(self):
        ''' Read tagged doc from mutliple files (sents, tokens, concepts, links, tags) '''
        if not os.path.isfile(self.sent_path):
            raise Exception("Sentence file could not be found {}".format(self.sent_path))
        sent_rows = CSV.read_tsv(self.sent_path)
        for sid, text in sent_rows:
            self.new_sent(text.strip(), ID=sid)
        # Read tokens if available
        if os.path.isfile(self.token_path):
            sent_tokens_map = dd(list)
            token_rows = CSV.read_tsv(self.token_path)
            for token_row in token_rows:
                if len(token_row) == 6:
                    sid, wid, token, lemma, pos, comment = token_row
                else:
                    sid, wid, token, lemma, pos = token_row
                    comment = ''
                sent_tokens_map[sid].append((token, lemma, pos.strip(), wid, comment))
                # TODO: verify wid?
            # import tokens
            for sent in self.__sents:
                sent_tokens = sent_tokens_map[sent.ID]
                sent.import_tokens([x[0] for x in sent_tokens])
                for ((tk, lemma, pos, wid, comment), token) in zip(sent_tokens, sent.tokens):
                    token.pos = pos
                    token.lemma = lemma
                    token.comment = comment
                    token.new_tag(label=wid, tagtype='wid')
            # only read concepts if tokens are available
            if os.path.isfile(self.concept_path):
                # read concepts
                concept_rows = CSV.read_tsv(self.concept_path)
                for concept_row in concept_rows:
                    if len(concept_row) == 5:
                        sid, cid, clemma, tag, comment = concept_row
                    else:
                        sid, cid, clemma, tag = concept_row
                        comment = ''
                    self.__sent_map[sid].new_concept(tag.strip(), clemma=clemma, ID=cid, comment=comment)
                # only read concept-token links if tokens and concepts are available
                link_rows = CSV.read_tsv(self.link_path)
                for sid, cid, wid in link_rows:
                    sent = self.__sent_map[sid]
                    wid = int(wid.strip())
                    sent.concept(cid).add_token(sent[wid])
        # read sentence level tags
        if os.path.isfile(self.tag_path):
            rows = CSV.read_tsv(self.tag_path)
            for sid, cfrom, cto, label, tagtype in rows:
                self.__sent_map[sid].new_tag(label, cfrom, cto, tagtype=tagtype)
        return self

    def write_ttl_streams(self, sent_stream, token_stream, concept_stream, link_stream, tag_stream):
        # export to TTL format (multiple text files)
        sent_writer = csv.writer(sent_stream, dialect=STD_DIALECT, quoting=STD_QUOTING)
        token_writer = csv.writer(token_stream, dialect=STD_DIALECT, quoting=STD_QUOTING)
        concept_writer = csv.writer(concept_stream, dialect=STD_DIALECT, quoting=STD_QUOTING)
        link_writer = csv.writer(link_stream, dialect=STD_DIALECT, quoting=STD_QUOTING)
        tag_writer = csv.writer(tag_stream, dialect=STD_DIALECT, quoting=STD_QUOTING)
        for sent in self:
            sent_writer.writerow((sent.ID, sent.text))
            # write tokens
            for wid, token in enumerate(sent.tokens):
                token_writer.writerow((token.sent.ID, wid, token.text or token.surface(), token.lemma, token.pos, token.comment))
            # write concepts & wclinks
            for cid, concept in enumerate(sent.concepts):
                # write concept
                concept_writer.writerow((sent.ID, cid, concept.clemma, concept.tag, concept.comment))
                # write cwlinks
                for token in concept.tokens:
                    wid = sent.tokens.index(token)
                    link_writer.writerow((sent.ID, cid, wid))
            # write tags
            for tag in sent.tags:
                tag_writer.writerow((sent.ID, tag.cfrom, tag.cto, tag.label, tag.tagtype))

    def write_ttl(self):
        with FileHub(working_dir=self.path, default_mode='w') as output:
            self.write_ttl_streams(output[self.sent_path],
                                   output[self.token_path],
                                   output[self.concept_path],
                                   output[self.link_path],
                                   output[self.tag_path])

    @staticmethod
    def read_ttl(path):
        ''' Helper function to read Document in TTL format (i.e. ${docname}_*.txt)
        E.g. Document.read_ttl('~/data/myfile') is the same as Document('myfile', '~/data/').read()
        '''
        doc_path = os.path.dirname(path)
        doc_name = os.path.basename(path)
        return Document(doc_name, doc_path).read()

    @staticmethod
    def from_json_file(path):
        if not os.path.isfile(path):
            raise Exception("Document file could not be found: {}".format(path))
        doc_name = os.path.basename(path)
        doc_path = os.path.dirname(path)
        doc = Document(doc_name, path=doc_path)
        with open(path, 'rt') as infile:
            for line in infile:
                j = json.loads(line)
                sent = Sentence.from_json(j)
                doc.sents.append(sent)
                doc.sent_map[sent.ID] = sent
        return doc
