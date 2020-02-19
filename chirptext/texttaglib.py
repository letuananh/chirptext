# -*- coding: utf-8 -*-

''' Text Annotation module

Latest version can be found at https://github.com/letuananh/chirptext

:copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
:license: MIT, see LICENSE for more details.
'''

import os
import logging
import json
import csv
import warnings
from collections import namedtuple
from collections import defaultdict as dd
from collections import OrderedDict

from .anhxa import IDGenerator
from .leutile import FileHelper
from .anhxa import DataObject
from . import chio
from .chio import iter_tsv_stream


# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

STD_DIALECT = 'excel-tab'
STD_QUOTING = csv.QUOTE_MINIMAL
MODE_TSV = 'tsv'
MODE_JSON = 'json'
TokenInfo = namedtuple("TokenInfo", ['text', 'sk'])


def getLogger():
    return logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------

class Tag(DataObject):

    ''' A general tag which can be used for annotating different linguistic feature '''
    NONE = ''
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

    def __init__(self, label='', cfrom=-1, cto=-1, tagtype='', source=NONE, **kwargs):
        super().__init__(**kwargs)
        self.__cfrom = cfrom
        self.__cto = cto
        self.label = label
        self.source = source
        self.tagtype = tagtype  # tag type

    @property
    def cfrom(self):
        return self.__cfrom

    @cfrom.setter
    def cfrom(self, value):
        self.__cfrom = int(value) if value is not None else None

    @property
    def cto(self):
        return self.__cto

    @cto.setter
    def cto(self, value):
        self.__cto = int(value) if value is not None else None

    @property
    def type(self):
        ''' Alias for tagtype '''
        return self.tagtype

    @type.setter
    def type(self, value):
        self.tagtype = value

    @property
    def text(self):
        ''' Alias for label '''
        return self.label

    @text.setter
    def text(self, value):
        self.label = value

    def __repr__(self):
        if not self.tagtype:
            return '`{}`'.format(self.label)
        else:
            return '`{}:{}`'.format(self.tagtype, self.label)

    def __str__(self):
        return "`{l}`<{f}:{t}>{v}".format(l=self.label, f=self.cfrom, t=self.cto, v=self.tagtype)

    def to_json(self, default_cfrom=-1, default_cto=-1):
        a_dict = {'label': self.label}
        if self.tagtype:
            a_dict['type'] = self.tagtype
        if self.source:
            a_dict['source'] = self.source
        if self.cfrom is not None and self.cfrom != default_cfrom and self.cfrom >= 0:
            a_dict['cfrom'] = self.cfrom
        if self.cto is not None and self.cto != default_cto and self.cto >= 0:
            a_dict['cto'] = self.cto
        return a_dict

    @staticmethod
    def from_json(json_dict):
        tag = Tag()
        tag.update(json_dict, 'cfrom', 'cto', 'label', 'source', 'type')
        return tag


class Sentence(DataObject):

    def __init__(self, text='', ID=None, tokens=None, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.ID = ID
        self.__tags = []
        self.__tokens = []
        self.__concepts = []
        self.__concept_map = OrderedDict()  # concept.ID to concept object
        if tokens:
            self.tokens = tokens

    @property
    def ID(self):
        return self.__ID

    @ID.setter
    def ID(self, value):
        self.__ID = int(value) if value else None

    def __repr__(self):
        return str(self)

    def __str__(self):
        # return format_tag(self)
        if self.ID:
            return "#{id}: {txt}".format(id=self.ID, txt=self.text)
        else:
            return self.text

    def __getitem__(self, idx):
        return self.__tokens[int(idx)]

    def __len__(self):
        return len(self.__tokens)

    @property
    def tags(self):
        ''' Sentence level tags '''
        return self.__tags

    def tagmap(self):
        tm = dd(list)
        for t in self.tags:
            tm[t.tagtype].append(t)
        return tm

    @property
    def tokens(self):
        return self.__tokens

    @tokens.setter
    def tokens(self, tokens):
        if self.__tokens:
            raise Exception("Cannot import tokens as my token list is not empty")
        else:
            self.import_tokens(tokens)

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
        if tag.cfrom is not None and tag.cto is not None and tag.cfrom >= 0 and tag.cto >= 0:
            return self.text[tag.cfrom:tag.cto]
        else:
            return ''

    def new_tag(self, label, cfrom=-1, cto=-1, tagtype='', **kwargs):
        ''' Create a sentence-level tag '''
        tag_obj = Tag(label, cfrom, cto, tagtype=tagtype, **kwargs)
        return self.add_tag(tag_obj)

    def get_tag(self, tagtype, auto_create=False, **kwargs):
        ''' Get the first tag with a type in this sentence
            use get_tag('mytype', default='somevalue') to get a new tag with default value 
            when there is no tag with this type. This new tag object will NOT be stored in the current sentence by default.
           
            use auto_create=True to auto create a new tag in the current sentence using the 'default' value.
            If there is no default value provided, an empty string '' will be used.
        '''
        for t in self.__tags:
            if t.tagtype == tagtype:
                return t
        if auto_create:
            return self.new_tag(label='' if 'default' not in kwargs else kwargs['default'], tagtype=tagtype, **kwargs)
        elif 'default' in kwargs:
            return Tag(label=kwargs['default'], tagtype=tagtype, **kwargs)
        else:
            raise LookupError("Sentence {} was not tagged with the speficied tagtype ({})".format(self, tagtype))

    def get_tags(self, tagtype, **kwargs):
        ''' Get all tags of a type '''
        return [t for t in self.__tags if t.tagtype == tagtype]

    def add_tag(self, tag_obj):
        ''' Add an existing tag object into this sentence '''
        self.tags.append(tag_obj)
        return tag_obj

    def new_token(self, *args, **kwargs):
        tk = Token(*args, **kwargs)
        return self.add_token_object(tk)

    def add_token_object(self, token):
        ''' Add a token object into this sentence '''
        token.sent = self  # take ownership of given token
        self.__tokens.append(token)
        return token

    def new_concept_id(self):
        ID = 0
        while ID in self.__concept_map:
            ID += 1
        return ID

    def new_concept(self, tag, clemma="", tokens=None, cidx=None, **kwargs):
        ''' Create a new concept object and add it to concept list
        tokens can be a list of Token objects or token indices
        '''
        if cidx is None:
            cidx = self.new_concept_id()
        if tokens:
            tokens = (t if isinstance(t, Token) else self[t] for t in tokens)
        c = Concept(cidx=cidx, tag=tag, clemma=clemma, sent=self, tokens=tokens, **kwargs)
        return self.add_concept(c)

    def add_concept(self, concept_obj):
        ''' Add a concept to current concept list '''
        if concept_obj is None:
            raise Exception("Concept object cannot be None")
        elif concept_obj in self.__concepts:
            raise Exception("Concept object is already inside")
        elif concept_obj.cidx in self.__concept_map:
            raise Exception("Duplicated concept ID ({})".format(concept_obj.cidx))
        self.__concepts.append(concept_obj)
        self.__concept_map[concept_obj.cidx] = concept_obj
        concept_obj.sent = self
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

    def concept(self, cid, **kwargs):
        ''' Get concept by concept ID '''
        if cid not in self.__concept_map:
            if 'default' in kwargs:
                return kwargs['default']
            else:
                raise KeyError("Invalid cid")
        else:
            return self.__concept_map[cid]

    def to_json(self):
        sent_dict = {'text': self.text}
        if self.tokens:
            sent_dict['tokens'] = [t.to_json() for t in self.tokens]
        if self.concepts:
            sent_dict['concepts'] = [c.to_json() for c in self.concepts]
        if self.ID is not None:
            sent_dict['ID'] = self.ID
        if self.flag is not None:
            sent_dict['flag'] = self.flag
        if self.comment is not None:
            sent_dict['comment'] = self.comment
        if self.__tags:
            sent_dict['tags'] = [t.to_json() for t in self.__tags]
        return sent_dict

    def import_tokens(self, tokens, import_hook=None, ignorecase=True):
        ''' Import a list of string as tokens '''
        text = self.text.lower() if ignorecase else self.text
        has_hooker = import_hook and callable(import_hook)
        cfrom = 0
        if self.__tokens:
            for tk in self.__tokens:
                if tk.cfrom and tk.cfrom > cfrom:
                    cfrom = tk.cfrom
        for token in tokens:
            if has_hooker:
                import_hook(token)
            to_find = token.lower() if ignorecase else token
            start = text.find(to_find, cfrom)
            # stanford parser
            if to_find == '``' or to_find == "''":
                start_dq = text.find('"', cfrom)
                if start_dq > -1 and (start == -1 or start > start_dq):
                    to_find = '"'
                    start = start_dq
            if to_find == '`' or to_find == "'":
                start_dq = text.find("'", cfrom)
                if start_dq > -1 and (start == -1 or start > start_dq):
                    to_find = "'"
                    start = start_dq
            if start == -1:
                raise LookupError('Cannot find token `{t}` in sent `{s}`({l}) from {i} ({p})'.format(t=token, s=self.text, l=len(self.text), i=cfrom, p=self.text[cfrom:cfrom + 20]))
            cfrom = start
            cto = cfrom + len(to_find)
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
        sent.update(json_sent, 'ID', 'comment', 'flag')
        # import tokens
        for json_token in json_sent.get('tokens', []):
            sent.add_token_object(Token.from_json(json_token))
        # import concepts
        for json_concept in json_sent.get('concepts', []):
            tag = json_concept['tag']
            clemma = json_concept['clemma']
            tokenids = json_concept['tokens']
            concept = sent.new_concept(tag, clemma=clemma, tokens=tokenids)
            concept.update(json_concept, Concept.COMMENT, Concept.FLAG)
        for json_tag in json_sent.get('tags', []):
            sent.add_tag(Tag.from_json(json_tag))
        return sent


class Token(DataObject):

    def __init__(self, text='', cfrom=-1, cto=-1, sent=None, pos=None, lemma=None, comment=None, **kwargs):
        ''' A token (e.g. a word in a sentence) '''
        super().__init__(**kwargs)
        self.sent = sent
        self.__tags = []
        self.cfrom = cfrom
        self.cto = cto
        self.text = text  # original form
        self.lemma = lemma   # dictionary form
        self.pos = pos
        self.comment = comment

    def __getitem__(self, idx):
        return self.__tags[idx]

    def __len__(self):
        return len(self.__tags)

    def __iter__(self):
        return iter(self.__tags)

    @property
    def tags(self):
        return self.__tags

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

    def new_tag(self, label, cfrom=None, cto=None, tagtype=None, **kwargs):
        ''' Create a new tag on this token '''
        if cfrom is None:
            cfrom = self.cfrom
        if cto is None:
            cto = self.cto
        tag = Tag(label=label, cfrom=cfrom, cto=cto, tagtype=tagtype, **kwargs)
        return self.add_tag(tag)

    def get_tag(self, tagtype, auto_create=False, **kwargs):
        ''' Get the first tag with a type in this token
            use get_tag('mytype', default='somevalue') to get a new tag with default value 
            when there is no tag with this type. This new tag object will NOT be stored in the token by default.
           
            use auto_create=True to auto create a new tag in the current token using the 'default' value.
            If there is no default value provided, an empty string '' will be used.
        '''
        for t in self.__tags:
            if t.tagtype == tagtype:
                return t
        if auto_create:
            return self.new_tag(label='' if 'default' not in kwargs else kwargs['default'], tagtype=tagtype, **kwargs)
        elif 'default' in kwargs:
            return Tag(label=kwargs['default'], tagtype=tagtype, **kwargs)
        else:
            raise LookupError("Token {} is not tagged with the speficied tagtype ({})".format(self, tagtype))

    def get_tags(self, tagtype, **kwargs):
        ''' Get all token-level tags with the specified tagtype '''
        return [t for t in self.__tags if t.tagtype == tagtype]

    def add_tag(self, tag_obj):
        ''' Add an existing tag object into this token '''
        self.__tags.append(tag_obj)
        return tag_obj

    def find(self, tagtype, **kwargs):
        ''' (Deprecated) Return the first tag with a given tagtype in this token '''
        warnings.warn("Token.find() is deprecated and will be removed in near future. Use Token.get_tag() instead", DeprecationWarning, stacklevel=2)
        return self.get_tag(tagtype, **kwargs)

    def find_all(self, tagtype, **kwargs):
        ''' (Deprecated) Find all token-level tags with the specified tagtype '''
        warnings.warn("Token.find_all() is deprecated and will be removed in near future. Use Token.get_tags() instead", DeprecationWarning, stacklevel=2)
        return self.get_tags(tagtype, **kwargs)

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
        if self.flag:
            token_json['flag'] = self.flag
        all_tags = [t.to_json(default_cfrom=self.cfrom, default_cto=self.cto) for t in self.tags]
        if all_tags:
            token_json['tags'] = all_tags
        return token_json

    @staticmethod
    def from_json(token_dict):
        tk = Token()
        tk.update(token_dict, 'cfrom', 'cto', 'text', 'lemma', 'pos', 'comment')
        # rebuild tags
        for tag_json in token_dict.get('tags', []):
            tk.add_tag(Tag.from_json(tag_json))
        return tk


class Concept(DataObject):

    FLAG = 'flag'
    COMMENT = 'comment'
    NOT_MATCHED = 'E'

    def __init__(self, cidx=None, tag='', clemma='', sent=None, tokens=None, comment=None, **kwargs):
        super().__init__(**kwargs)
        self.cidx = cidx
        self.sent = sent
        self.__tokens = []
        self.clemma = clemma
        self.tag = tag
        self.flag = None
        self.comment = comment if comment else ''
        if tokens:
            self.__tokens.extend(tokens)

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
            'tag': str(self.tag),
            'tokens': tokens
        }
        if self.comment:
            cdict[Concept.COMMENT] = self.comment
        if self.flag:
            cdict[Concept.FLAG] = self.flag
        return cdict


class Document(DataObject):

    def __init__(self, name='', path='.', **kwargs):
        super().__init__(**kwargs)
        self.__path = FileHelper.abspath(path)
        self.__name = name
        self.__sents = []
        self.__sent_map = {}
        self.__idgen = IDGenerator(id_hook=self.has_id)  # for creating a new sentence without ID

    def new_id(self):
        warnings.warn("new_id() is deprecated and will be removed in near future.", DeprecationWarning, stacklevel=2)
        return next(self.__idgen)

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value

    @property
    def path(self):
        return self.__path

    @path.setter
    def path(self, value):
        self.__path = value

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

    def __len__(self):
        return len(self.__sents)

    def __getitem__(self, idx):
        return self.__sents[idx]

    def get(self, sent_id, **kwargs):
        ''' If sent_id exists, remove and return the associated sentence object else return default.
        If no default is provided, KeyError will be raised.'''
        if sent_id is not None and not isinstance(sent_id, int):
            sent_id = int(sent_id)
        if sent_id is None or not self.has_id(sent_id):
            if 'default' in kwargs:
                return kwargs['default']
            else:
                raise KeyError("Invalid sentence ID ({})".format(sent_id))
        return self.__sent_map[sent_id]

    def has_id(self, sent_id):
        return int(sent_id) in self.__sent_map

    def add_sent(self, sent_obj):
        ''' Add a ttl.Sentence object to this document '''
        if sent_obj is None:
            raise Exception("Sentence object cannot be None")
        elif sent_obj.ID is None:
            # if sentID is None, create a new ID
            sent_obj.ID = next(self.__idgen)
        elif self.has_id(sent_obj.ID):
            raise Exception("Sentence ID {} exists".format(sent_obj.ID))
        self.__sent_map[sent_obj.ID] = sent_obj
        self.__sents.append(sent_obj)
        return sent_obj

    def new_sent(self, text, ID=None, **kwargs):
        ''' Create a new sentence and add it to this Document '''
        if ID is None:
            ID = next(self.__idgen)
        return self.add_sent(Sentence(text, ID=ID, **kwargs))

    def pop(self, sent_id, **kwargs):
        ''' If sent_id exists, remove and return the associated sentence object else return default.
        If no default is provided, KeyError will be raised.'''
        if sent_id is not None and not isinstance(sent_id, int):
            sent_id = int(sent_id)
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
        warnings.warn("Document.read() is deprecated and will be removed in near future.", DeprecationWarning, stacklevel=2)
        with TxtReader.from_doc(self) as reader:
            reader.read(self)
        return self

    @staticmethod
    def read_ttl(path):
        ''' Helper function to read Document in TTL-TXT format (i.e. ${docname}_*.txt)
        E.g. Document.read_ttl('~/data/myfile') is the same as Document('myfile', '~/data/').read()
        '''
        warnings.warn("Document.read_ttl() is deprecated and will be removed in near future. Use read() instead", DeprecationWarning, stacklevel=2)
        doc_path = os.path.dirname(path)
        doc_name = os.path.basename(path)
        return Document(doc_name, doc_path).read()

    def write_ttl(self):
        ''' Helper function to write doc to TTL-TXT format '''
        with TxtWriter.from_doc(self) as writer:
            writer.write_doc(self)

    @staticmethod
    def from_json_file(path):
        warnings.warn("Document.from_json_file() is deprecated and will be removed in near future.", DeprecationWarning, stacklevel=2)
        return read_json(path)


class TxtReader(object):
    def __init__(self, sent_stream, token_stream, concept_stream, link_stream, tag_stream, doc_name='', doc_path='.'):
        self.sent_stream = sent_stream
        self.token_stream = token_stream
        self.concept_stream = concept_stream
        self.link_stream = link_stream
        self.tag_stream = tag_stream
        self.doc_name = doc_name
        self.doc_path = doc_path

    def sent_reader(self):
        return iter_tsv_stream(self.sent_stream) if self.sent_stream else None

    def token_reader(self):
        return iter_tsv_stream(self.token_stream) if self.token_stream else None

    def concept_reader(self):
        return iter_tsv_stream(self.concept_stream) if self.concept_stream else None

    def link_reader(self):
        return iter_tsv_stream(self.link_stream) if self.link_stream else None

    def tag_reader(self):
        return iter_tsv_stream(self.tag_stream) if self.tag_stream else None

    @staticmethod
    def from_path(path):
        doc_path = os.path.dirname(path)
        doc_name = os.path.basename(path)
        doc = Document(name=doc_name, path=doc_path)
        return TxtReader.from_doc(doc)

    @staticmethod
    def from_doc(doc, encoding='utf-8'):
        reader = TxtReader(sent_stream=open(doc.sent_path, mode='rt', encoding=encoding),
                           token_stream=open(doc.token_path, mode='rt', encoding=encoding) if doc.token_path else None,
                           concept_stream=open(doc.concept_path, mode='rt', encoding=encoding) if doc.concept_path else None,
                           link_stream=open(doc.link_path, mode='rt', encoding=encoding) if doc.link_path else None,
                           tag_stream=open(doc.tag_path, mode='rt', encoding=encoding) if doc.tag_path else None,
                           doc_name=doc.name,
                           doc_path=doc.path)
        return reader

    def close(self):
        self.sent_stream.close()
        self.token_stream.close()
        self.concept_stream.close()
        self.link_stream.close()
        self.tag_stream.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def read(self, doc=None):
        ''' Read tagged doc from mutliple files (sents, tokens, concepts, links, tags) '''
        if not self.sent_stream:
            raise Exception("There is no sentence data stream available")
        if doc is None:
            doc = Document(name=self.doc_name, path=self.doc_path)
        for row in self.sent_reader():
            if len(row) == 2:
                sid, text = row
                doc.new_sent(text.strip(), ID=sid)
            elif len(row) == 4:
                sid, text, flag, comment = row
                sent = doc.new_sent(text.strip(), ID=sid)
                sent.flag = flag
                sent.comment = comment
        # Read tokens if available
        if self.token_stream:
            # read all tokens first
            sent_tokens_map = dd(list)
            for token_row in self.token_reader():
                if len(token_row) == 6:
                    sid, wid, token, lemma, pos, comment = token_row
                else:
                    sid, wid, token, lemma, pos = token_row
                    comment = ''
                sid = int(sid)
                sent_tokens_map[sid].append((token, lemma, pos.strip(), wid, comment))
                # TODO: verify wid?
            # import tokens
            for sent in doc:
                sent_tokens = sent_tokens_map[sent.ID]
                sent.import_tokens([x[0] for x in sent_tokens])
                for ((tk, lemma, pos, wid, comment), token) in zip(sent_tokens, sent.tokens):
                    token.pos = pos
                    token.lemma = lemma
                    token.comment = comment
            # only read concepts if tokens are available
            if self.concept_stream:
                # read concepts
                for concept_row in self.concept_reader():
                    if len(concept_row) == 5:
                        sid, cid, clemma, tag, comment = concept_row
                    else:
                        sid, cid, clemma, tag = concept_row
                        comment = ''
                    cid = int(cid)
                    doc.get(sid).new_concept(tag.strip(), clemma=clemma, cidx=cid, comment=comment)
                # only read concept-token links if tokens and concepts are available
                for sid, cid, wid in self.link_reader():
                    sent = doc.get(sid)
                    cid = int(cid)
                    wid = int(wid.strip())
                    sent.concept(cid).add_token(sent[wid])
        # read sentence level tags
        if self.tag_stream:
            for row in self.tag_reader():
                if len(row) == 5:
                    sid, cfrom, cto, label, tagtype = row
                    wid = None
                if len(row) == 6:
                    sid, cfrom, cto, label, tagtype, wid = row
                if cfrom:
                    cfrom = int(cfrom)
                if cto:
                    cto = int(cto)
                if wid is None or wid == '':
                    doc.get(sid).new_tag(label, cfrom, cto, tagtype=tagtype)
                else:
                    doc.get(sid)[int(wid)].new_tag(label, cfrom, cto, tagtype=tagtype)
        return doc


class TxtWriter(object):
    def __init__(self, sent_stream, token_stream, concept_stream, link_stream, tag_stream, id_seed=1):
        self.sent_stream = sent_stream
        self.token_stream = token_stream
        self.concept_stream = concept_stream
        self.link_stream = link_stream
        self.tag_stream = tag_stream
        self.sent_writer = csv.writer(sent_stream, dialect=STD_DIALECT, quoting=STD_QUOTING)
        self.token_writer = csv.writer(token_stream, dialect=STD_DIALECT, quoting=STD_QUOTING)
        self.concept_writer = csv.writer(concept_stream, dialect=STD_DIALECT, quoting=STD_QUOTING)
        self.link_writer = csv.writer(link_stream, dialect=STD_DIALECT, quoting=STD_QUOTING)
        self.tag_writer = csv.writer(tag_stream, dialect=STD_DIALECT, quoting=STD_QUOTING)
        self.__idgen = IDGenerator(id_seed=id_seed)

    def write_sent(self, sent, **kwargs):
        flag = sent.flag if sent.flag is not None else ''
        comment = sent.comment if sent.comment is not None else ''
        sid = sent.ID if sent.ID is not None else next(self.__idgen)
        self.sent_writer.writerow((sid, sent.text, flag, comment))
        # write tokens
        for wid, token in enumerate(sent.tokens):
            self.token_writer.writerow((sid, wid, token.text or token.surface(), token.lemma, token.pos, token.comment))
        # write concepts & wclinks
        for cid, concept in enumerate(sent.concepts):
            # write concept
            self.concept_writer.writerow((sid, cid, concept.clemma, concept.tag, concept.comment))
            # write cwlinks
            for token in concept.tokens:
                wid = sent.tokens.index(token)
                self.link_writer.writerow((sid, cid, wid))
        # write tags
        for tag in sent.tags:
            self.tag_writer.writerow((sid, tag.cfrom, tag.cto, tag.label, tag.tagtype, ''))
        # write token-level tags
        for wid, token in enumerate(sent.tokens):
            for tag in token:
                self.tag_writer.writerow((sid, tag.cfrom, tag.cto, tag.label, tag.tagtype, wid))

    def write_doc(self, doc, **kwargs):
        for sent in doc:
            self.write_sent(sent)

    def close(self):
        self.sent_stream.close()
        self.token_stream.close()
        self.concept_stream.close()
        self.link_stream.close()
        self.tag_stream.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @staticmethod
    def from_doc(doc, encoding='utf-8', **kwargs):
        return TxtWriter(sent_stream=open(doc.sent_path, mode='wt', encoding=encoding),
                         token_stream=open(doc.token_path, mode='wt', encoding=encoding),
                         concept_stream=open(doc.concept_path, mode='wt', encoding=encoding),
                         link_stream=open(doc.link_path, mode='wt', encoding=encoding),
                         tag_stream=open(doc.tag_path, mode='wt', encoding=encoding), **kwargs)

    @staticmethod
    def from_path(path, **kwargs):
        doc_path = os.path.dirname(path)
        doc_name = os.path.basename(path)
        doc = Document(name=doc_name, path=doc_path)
        return TxtWriter.from_doc(doc, **kwargs)


class JSONWriter(object):
    def __init__(self, output_stream, id_seed=1, **kwargs):
        self.__output_stream = output_stream
        self.__idgen = IDGenerator(id_seed=id_seed)

    def write_sent(self, sent, ensure_ascii=False, **kwargs):
        if sent.ID is None:
            sent.ID = next(self.__idgen)
        self.__output_stream.write(json.dumps(sent.to_json(), ensure_ascii=ensure_ascii))
        self.__output_stream.write('\n')

    def write_doc(self, doc, ensure_ascii=False, **kwargs):
        for sent in doc:
            self.write_sent(sent, ensure_ascii=ensure_ascii)

    def close(self):
        try:
            if self.__output_stream is not None:
                self.__output_stream.flush()
                self.__output_stream.close()
                self.__output_stream = None
        except:
            getLogger().exception("Could not close JSONWriter's output stream properly")

    @staticmethod
    def from_path(path, id_seed=1, **kwargs):
        return JSONWriter(output_stream=chio.open(path, mode='wt', **kwargs), id_seed=id_seed)

    @staticmethod
    def from_doc(doc, **kwargs):
        doc_path = os.path.join(doc.path, doc.name + '.ttl.json')
        return JSONWriter.from_path(doc_path, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ------------------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------------------
def read_json_iter(path):
    if not os.path.isfile(path):
        raise Exception("Document file could not be found: {}".format(path))
    with chio.open(path) as infile:
        for line in infile:
            j = json.loads(line)
            sent = Sentence.from_json(j)
            yield sent
    return


def read_json(path):
    if not os.path.isfile(path):
        raise Exception("Document file could not be found: {}".format(path))
    doc_name = os.path.splitext(os.path.basename(path))[0]
    doc_path = os.path.dirname(path)
    doc = Document(doc_name, path=doc_path)
    for sent in read_json_iter(path):
        doc.add_sent(sent)
    return doc


def write_json(path, doc, ensure_ascii=False, **kwargs):
    with JSONWriter.from_path(path) as writer:
        writer.write_doc(doc, ensure_ascii=ensure_ascii, **kwargs)


def read(path, mode='tsv'):
    ''' Helper function to read Document in TTL-TXT format (i.e. ${docname}_*.txt)
    E.g. read('~/data/myfile') is the same as Document('myfile', '~/data/').read()
    '''
    if mode == 'tsv':
        doc_path = os.path.dirname(path)
        doc_name = os.path.basename(path)
        doc = Document(name=doc_name, path=doc_path)
        reader = TxtReader.from_doc(doc)
        doc = reader.read(doc=doc)
        reader.close()
        return doc
    elif mode == 'json':
        return read_json(path)
    else:
        raise Exception("Invalid mode - [{}] was provided".format(mode))


def write(path, doc, mode=MODE_TSV, **kwargs):
    ''' Helper function to write doc to TTL-TXT format '''
    if mode == MODE_TSV:
        with TxtWriter.from_path(path) as writer:
            writer.write_doc(doc)
    elif mode == MODE_JSON:
        write_json(path, doc, **kwargs)
