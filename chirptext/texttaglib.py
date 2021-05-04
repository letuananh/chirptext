# -*- coding: utf-8 -*-

""" Text Annotation (texttaglib - TTL) module
"""

# Latest version can be found at https://github.com/letuananh/chirptext
# :copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import csv
import json
import logging
import os
import warnings
from collections import OrderedDict
from collections import defaultdict as dd
from typing import TypeVar, Generic, Sequence

from . import chio
from .anhxa import DataObject
from .anhxa import IDGenerator
from .chio import iter_tsv_stream
from .leutile import FileHelper


MODE_TSV = 'tsv'
MODE_JSON = 'json'


class Tag(DataObject):

    """ A general tag which can be used for annotating linguistic objects such as Sentence, Chunk, or Token """
    GOLD = 'gold'
    NONE = ''
    DEFAULT = 'n/a'
    MFS = 'mfs'  # most frequent sense
    WORDNET = 'wn'
    OTHER = 'other'
    NLTK = 'nltk'
    ISF = 'isf'  # integrated semantic framework: https://github.com/letuananh/intsem.fx
    MECAB = "mecab"

    def __init__(self, value='', type=NONE, cfrom=-1, cto=-1, source=NONE, **kwargs):
        super().__init__(**kwargs)
        self.value = value
        self.type = type  # tag type
        self.__cfrom = cfrom
        self.__cto = cto
        self.source = source

    @property
    def cfrom(self):
        """ starting character index of a Tag """
        return self.__cfrom

    @cfrom.setter
    def cfrom(self, value):
        self.__cfrom = int(value) if value is not None else None

    @property
    def cto(self):
        """ ending character index of a Tag """
        return self.__cto

    @cto.setter
    def cto(self, value):
        self.__cto = int(value) if value is not None else None

    @property
    def text(self):
        """ Alias for Tag.value """
        return self.value

    @text.setter
    def text(self, value):
        self.value = value

    def __repr__(self):
        if not self.type:
            return f'Tag(value={repr(self.value)})'
        else:
            return f'Tag(value={repr(self.value)}, type={repr(self.type)})'

    def __str__(self):
        if self.cfrom not in (-1, None) and self.cto not in (-1, None):
            return "`{l}`<{f}:{t}>{v}".format(l=self.value, f=self.cfrom, t=self.cto, v=self.type)
        else:
            return f"{self.type}/{self.value}"

    def to_dict(self, default_cfrom=-1, default_cto=-1, *args, **kwargs):
        """ Serialize this Tag object data into a dict """
        a_dict = {'value': self.value}
        if self.type:
            a_dict['type'] = self.type
        if self.source:
            a_dict['source'] = self.source
        if self.cfrom is not None and self.cfrom != -1 and self.cfrom != default_cfrom and self.cfrom >= 0:
            a_dict['cfrom'] = self.cfrom
        if self.cto is not None and self.cto != -1 and self.cto != default_cto and self.cto >= 0:
            a_dict['cto'] = self.cto
        return a_dict

    @staticmethod
    def from_dict(json_dict):
        """ Create a Tag object from a dict's data """
        tag = Tag()
        tag.update(json_dict, 'cfrom', 'cto', 'value', 'source', 'type')
        return tag


T = TypeVar('TagType')


class TagSet(Generic[T]):
    """ contains all tags of a linguistic object """

    class TagMap:
        def __init__(self, tagset):
            self.__dict__["_TagMap__tagset"] = tagset

        def __getitem__(self, type) -> T:
            """ Get the first tag object in the tag list of a given type if exist, else return None """
            if type in self.__tagset and len(self.__tagset[type]) > 0:
                return self.__tagset[type][0]
            else:
                return None

        def __setitem__(self, type, value):
            """ Set the first tag object in the tag list of a given type to key if exist, else create a new tag """
            _old = self[type]
            if not _old:
                # create a new tag
                self.__tagset.add(value=value, type=type)
            else:
                # pop the old tag and replace it with a new one
                self.__tagset.replace(_old, value=value, type=type)

        def __getattr__(self, type) -> T:
            """ get the first tag object in the tag list of a given type if exist, else return None """
            return self[type]

        def __setattr__(self, type, value):
            """ Set the first tag object in the tag list of a given type to key if exist, else create a new tag """
            self[type] = value

    def __init__(self, parent=None, **kwargs):
        self.__parent = parent
        self.__proto_kwargs = kwargs['proto_kwargs'] if 'proto_kwargs' in kwargs else {}
        self.__proto = kwargs['proto'] if 'proto' in kwargs else Tag
        self.__dict__["_TagSet__tags"] = []
        self.__dict__["_TagSet__tagmap"] = TagSet.TagMap(self)
        self.__dict__["_TagSet__tagsmap"] = dd(list)

    @property
    def gold(self):
        """ Interact with first tag (gold) directly """
        return self.__tagmap

    def __len__(self):
        """ Number of tags in this object """
        return len(self.__tags)

    def __getitem__(self, type) -> T:
        """ Get the all tags of a given type """
        return self.__tagsmap[type]

    def __getattr__(self, type) -> T:
        """ Get the first tag of a given type if it exists"""
        return self[type]

    def __contains__(self, type):
        """ Check if there is at least a tag with a type """
        return type in self.__tagsmap

    def __iter__(self) -> T:
        """ Loop through all tags in this set """
        return iter(self.__tags)

    def items(self):
        """ Return an iterator to loop through all (type, value_list) pairs in this TagSet """
        return self.__tagsmap.items()

    def _construct_tag(self, *args, **kwargs) -> T:
        """ Construct a new tag object and notify parent if possible """
        if self.__proto_kwargs:
            # prioritise values in kwargs rather than in default constructor kwargs
            for k, v in self.__proto_kwargs.items():
                if k not in self.kwargs:
                    kwargs[k] = v
        _tag = self.__proto(*args, **kwargs)
        if self.__parent:
            self.__parent._claim(_tag)
        return _tag

    def add(self, value, type='', *args, **kwargs) -> T:
        """ Create a new generic tag object """
        if not value and not type:
            raise ValueError("Concept value and type cannot be both empty")
        _tag = self._construct_tag(value=value, type=type, *args, **kwargs)
        self.__tags.append(_tag)
        self.__tagsmap[_tag.type].append(_tag)
        return _tag

    def replace(self, old_tag, value, type='', *args, **kwargs) -> T:
        """ Create a new tag to replace an existing tag object """
        self.__tags.remove(old_tag)
        new_tag = self._construct_tag(value=value, type=type, *args, **kwargs)
        self.__tags.append(new_tag)
        if old_tag.type == new_tag.type:
            _taglist = self.__tagsmap[old_tag.type]
            _taglist[_taglist.index(old_tag)] = new_tag
        else:
            self.__tagsmap[old_tag.type].remove(old_tag)
            self.__tagsmap[new_tag.type].append(new_tag)
        return new_tag

    def remove(self, tag: T) -> T:
        """ Remove a generic tag object and return them """
        if tag is None:
            raise ValueError("Null tag object cannot be popped")
        elif tag.type not in self:
            raise ValueError("This tag object does not exist in this TagSet")
        else:
            self.__tagsmap[tag.type].remove(tag)
            self.__tags.remove(tag)
            return tag

    def pop(self, idx: int) -> T:
        """ Remove a tag at the given index and return it """
        return self.remove(self.__tags[idx])

    def values(self, type=None):
        """ Get all values of tags with the specified type or all tags when type is None """
        return (t.value for t in (self[type] if type is not None else self))

    def to_dict(self, *args, **kwargs):
        """ Create a list of dicts from all tag objects """
        return {"tags": [t.to_dict(*args, **kwargs) for t in self]}


class Token(DataObject):

    """ A sentence token (i.e. a word) """

    def __init__(self, text='', cfrom=-1, cto=-1, pos=None, lemma=None, comment=None, flag=None, **kwargs):
        """ A token (e.g. a word in a sentence) """
        super().__init__(**kwargs)
        self.__tags: TagSet[Tag] = TagSet[Tag](parent=self)
        self.cfrom = cfrom
        self.cto = cto
        self.text = text  # original/surface form
        self.lemma = lemma   # dictionary form
        self.pos = pos
        self.comment = comment
        self.flag = flag

    def __getitem__(self, idx):
        return self.__tags[idx]

    def __len__(self):
        return len(self.__tags)

    def __iter__(self):
        return iter(self.__tags)

    @property
    def tag(self):
        """ Interact with first tag (gold) directly """
        return self.__tags.gold

    @property
    def tags(self):
        """ Tag manager object of this sentence (list access) """
        return self.__tags

    def surface(self):
        """ Get the surface form of this token """
        # Prioritise self.text
        if self.text:
            return self.text
        elif self.sent and self.sent.text:
            return self.sent.text[self.cfrom:self.cto]
        else:
            return ''

    def __repr__(self):
        return "`{l}`<{f}:{t}>".format(l=self.text, f=self.cfrom, t=self.cto)

    def tag_map(self):
        """ Build a map from tagtype to list of tags """
        tm = dd(list)
        for tag in self.__tags:
            tm[tag.type].append(tag)
        return tm

    def __str__(self):
        return "`{l}`<{f}:{t}>{tgs}".format(l=self.text, f=self.cfrom, t=self.cto, tgs=self.__tags if self.__tags else '')

    def new_tag(self, label, cfrom=None, cto=None, tagtype=None, **kwargs):
        """ Create a new tag on this token """
        if cfrom is None:
            cfrom = self.cfrom
        if cto is None:
            cto = self.cto
        tag = Tag(value=label, type=tagtype, cfrom=cfrom, cto=cto, **kwargs)
        return self.add_tag(tag)

    def get_tag(self, tagtype, auto_create=False, **kwargs):
        """ Get the first tag with a type in this token
            use get_tag('mytype', default='somevalue') to get a new tag with default value
            when there is no tag with this type. This new tag object will NOT be stored in the token by default.

            use auto_create=True to auto create a new tag in the current token using the 'default' value.
            If there is no default value provided, an empty string '' will be used.
        """
        for t in self.__tags:
            if t.type == tagtype:
                return t
        if auto_create:
            return self.new_tag(label='' if 'default' not in kwargs else kwargs['default'], tagtype=tagtype, **kwargs)
        elif 'default' in kwargs:
            return Tag(value=kwargs['default'], type=tagtype, **kwargs)
        else:
            raise LookupError("Token {} is not tagged with the speficied tagtype ({})".format(self, tagtype))

    def get_tags(self, tagtype, **kwargs):
        """ Get all token-level tags with the specified tagtype """
        return [t for t in self.__tags if t.type == tagtype]

    def add_tag(self, tag_obj):
        """ Add an existing tag object into this token """
        self.__tags.append(tag_obj)
        return tag_obj

    def find(self, tagtype, **kwargs):
        """ (Deprecated) Return the first tag with a given tagtype in this token """
        warnings.warn("Token.find() is deprecated and will be removed in near future. Use Token.get_tag() instead", DeprecationWarning, stacklevel=2)
        return self.get_tag(tagtype, **kwargs)

    def find_all(self, tagtype, **kwargs):
        """ (Deprecated) Find all token-level tags with the specified tagtype """
        warnings.warn("Token.find_all() is deprecated and will be removed in near future. Use Token.get_tags() instead", DeprecationWarning, stacklevel=2)
        return self.get_tags(tagtype, **kwargs)

    def to_dict(self):
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
        all_tags = [t.to_dict(default_cfrom=self.cfrom, default_cto=self.cto) for t in self.tags]
        if all_tags:
            token_json['tags'] = all_tags
        return token_json

    @staticmethod
    def from_dict(token_dict):
        tk = Token()
        tk.update(token_dict, 'cfrom', 'cto', 'text', 'lemma', 'pos', 'comment')
        # rebuild tags
        for tag_json in token_dict.get('tags', []):
            tk.add_tag(Tag.from_dict(tag_json))
        return tk


class TokenList(list):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__parent = parent

    def add(self, *args, **kwargs):
        """ Create a new token and add this this TokenList """
        self.add_obj(Token(*args, sent=self.__parent, **kwargs))

    def add_obj(self, token):
        """ [Internal function] Add an existing Token object into this TokenList

        Currently this function is only used for constructing structures from input streams.
        General users should NOT use this function as it is very likely to be removed in the future
        """
        token.sent = self.__parent
        self.append(token)


class Concept(Tag):

    """ Represent a concept in an utterance, which may refers to multiple tokens """

    FLAG = 'flag'
    COMMENT = 'comment'
    NOT_MATCHED = 'E'

    def __init__(self, value='', type=None, clemma=None, tokens=None, comment=None, flag=None, **kwargs):
        super().__init__(value=value, type=type, **kwargs)
        self.clemma = clemma
        self.__tokens = []
        if tokens:
            self.add_token(*tokens)
        self.comment = comment
        self.flag = flag

    def add_token(self, *tokens):
        """ Add tokens to this concept """
        for token in tokens:
            if isinstance(token, Token):
                self.__tokens.append(token)
            elif isinstance(token, int) and self.sent is not None:
                self.__tokens.append(self.sent[token])
            else:
                raise ValueError(f"Invalid token value: {token} (Only token index and Token objects are accepted")

    def __getattr__(self, idx):
        """ Get the idx-th token of this concept """
        return self.__tokens[idx]

    def __iter__(self):
        """ Iterate through all tokens in this concept """
        return iter(self.__tokens)

    def __len__(self):
        """ Number of tokens belong to this concept """
        return len(self.__tokens)

    def __repr__(self):
        return '<{t}:"{l}">'.format(l=self.clemma, t=self.value)

    def __str__(self):
        return '<{t}:"{l}">({ws})'.format(l=self.clemma, t=self.value, ws=self.__tokens)

    def remove(self, token: Token):
        """ Remove a Token object from this concept """
        self.__tokens.remove(token)

    def pop(self, idx=None) -> Token:
        """ Remove a token from this concept and return it

        :param idx: the index of the token to be removed. If set to None (defaulted) idx of the last token will be used
        :type idx: int
        """
        if idx is None:
            return self.__tokens.pop()
        else:
            return self.__tokens.pop(idx)

    def to_dict(self, *args, **kwargs):
        concept_dict = super().to_dict(*args, **kwargs)
        if self.sent:
            # get token idx from sent
            concept_dict['tokens'] = [self.sent.tokens.index(t) for t in self.__tokens]
        else:
            concept_dict['tokens'] = [t.text for t in self.__tokens]
        if self.clemma is not None:
            concept_dict['clemma'] = self.clemma
        if self.type is not None:
            concept_dict['type'] = self.type
        if self.comment:
            concept_dict[Concept.COMMENT] = self.comment
        if self.flag:
            concept_dict[Concept.FLAG] = self.flag
        return concept_dict


class Sentence(DataObject):

    """ Represent an utterance (i.e. a sentence) """

    def __init__(self, text='', ID=None, tokens=None, **kwargs):
        super().__init__(text=text, ID=ID, **kwargs)
        self.__text = text
        self.__ID = ID
        self.__tags: TagSet[Tag] = TagSet[Tag](parent=self)
        self.__concepts: TagSet[Concept] = TagSet[Concept](proto=Concept, proto_kwargs={'sent': self})
        self.__tokens: TokenList = TokenList(parent=self)
        if tokens:
            self._import_tokens(tokens)

    @property
    def ID(self) -> str:
        """ ID string of a sentence """
        return self.__ID

    @ID.setter
    def ID(self, value):
        self.__ID = str(value) if value else None

    def __repr__(self):
        if self.ID:
            return f"Sentence(ID={repr(self.ID)}, text={repr(self.text)})"
        else:
            return f"Sentence({repr(self.text)})"

    def __str__(self):
        """ The text content of this sentence """
        return self.text

    def __getitem__(self, idx: int):
        """ Get the idx-th token in this sentence """
        return self.__tokens[idx]

    def __len__(self):
        """ Number of tokens in this sentence """
        return len(self.__tokens)

    @property
    def tags(self):
        """ Tag manager object of this sentence (list access) """
        return self.__tags

    @property
    def tag(self):
        """ Interact with first tag (gold) directly """
        return self.__tags.gold

    @property
    def concepts(self):
        """ Concept manager object of this sentence (list access) """
        return self.__concepts

    @property
    def concept(self):
        """ Interact with gold concept (gold) directly """
        return self.__concepts.gold

    @property
    def tokens(self):
        """ Access token list of this sentence """
        return self.__tokens

    @tokens.setter
    def tokens(self, tokens):
        if self.__tokens:
            raise Exception("Cannot import tokens as my token list is not empty")
        else:
            self._import_tokens(tokens)

    def surface(self, tag):
        """ Get surface string that is associated with a linguistic object """
        if tag.cfrom is not None and tag.cto is not None and tag.cfrom >= 0 and tag.cto >= 0:
            return self.text[tag.cfrom:tag.cto]
        else:
            return ''

    def tcmap(self, *concept_type):
        """ Create a token-concepts map

        :param concept_type: When provided, only concept with specified type(s) will be mapped
        """
        _tcmap = dd(list)
        for concept in self.__concepts:
            if concept_type and concept.type not in concept_type:
                continue
            else:
                for w in concept:
                    _tcmap[w].append(concept)
        return _tcmap

    def mwe(self, *concept_type):
        """ return an iterator of concepts that are linked to more than 1 token.

        # filter all Wordnet-based multi-word expressions
        >>> sent.mwe("WN")
        # filter senses from wordnets, Princeton Wordnet, and Open Multilingual Wordnet
        >>> sent.mwe("WN", "PWN", "OMW")
        # If you already have a type lise, try to use Python unpack syntax with
        >>> types = ["WN", "PWN", "OMW"]
        >>> sent.mwe(*types)

        :param concept_type: When provided, only concept with specified type(s) will be considered
        """
        if concept_type:
            return (c for c in self.__concepts if len(c.tokens) > 1 and c.type in concept_type)
        else:
            return (c for c in self.__concepts if len(c.tokens) > 1)

    def msw(self, *concept_type):
        """ Return a generator of tokens with more than one concept.

        :param concept_type: When provided, only concept with specified type(s) will be considered
        """
        return (t for t, c in self.tcmap(*concept_type).items() if len(c) > 1)

    def _claim(self, obj):
        """ [Internal function] claim ownership of an object """
        obj.sent = self

    def _import_tokens(self, tokens, import_hook=None, ignorecase=True):
        """ [Internal function ] Import a list of string as tokens

        General users should NOT use this function as it's very likely to be changed in the future
        """
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
            self.tokens.add(token, cfrom, cto)
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

    def to_dict(self, *args, **kwargs):
        """ Generate a JSON-ready dict that contains this sentence data
        """
        sent_dict = {'text': self.text}
        if self.tokens:
            sent_dict['tokens'] = [t.to_dict() for t in self.tokens]
        if self.concepts:
            sent_dict['concepts'] = [c.to_dict() for c in self.concepts]
        if self.ID is not None:
            sent_dict['ID'] = self.ID
        if self.flag is not None:
            sent_dict['flag'] = self.flag
        if self.comment is not None:
            sent_dict['comment'] = self.comment
        if self.__tags:
            sent_dict['tags'] = [t.to_dict() for t in self.__tags]
        return sent_dict

    @staticmethod
    def from_dict(json_sent):
        sent = Sentence(json_sent['text'])
        sent.update(json_sent, 'ID', 'comment', 'flag')
        # import tokens
        for json_token in json_sent.get('tokens', []):
            sent.tokens.add_obj(Token.from_dict(json_token))
        # import concepts
        for json_concept in json_sent.get('concepts', []):
            tag = json_concept['value']
            clemma = json_concept['clemma']
            tokenids = json_concept['tokens']
            concept = sent.new_concept(tag, clemma=clemma, tokens=tokenids)
            concept.update(json_concept, Concept.COMMENT, Concept.FLAG)
        # import sentence's tag
        for json_tag in json_sent.get('tags', []):
            sent.add_tag(Tag.from_dict(json_tag))
        return sent


class Document(DataObject):

    def __init__(self, name='', path='.', **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.path = path
        self.__sents = []
        self.__sent_map = {}
        self.__idgen = IDGenerator(id_hook=lambda x: x in self)  # for creating a new sentence without ID

    def __len__(self):
        return len(self.__sents)

    def __getitem__(self, sent_id):
        """ Get a sentence object by ID """
        return self.__sent_map[str(sent_id)]

    def __contains__(self, sent_id):
        """ Check if a given sentence ID exists in this Document """
        return str(sent_id) in self.__sent_map

    def __iter__(self):
        """ Return an iterator to loop though all sentences in this Document """
        return iter(self.__sents)

    def get(self, sent_id, **kwargs):
        """ Find sentence with a specific sent_id

        a kwargs = 'default' can be set to specify the default value to return when there is no matching sentence.
        If no default is provided, KeyError will be raised.

        >>> sent = doc.get("sent_id_does_not_exist", None)
        # sent is set to None instead of throwing KeyError

        :param sent_id: ID of the sentence to find
        :type: str
        :raises: KeyError
        """
        if sent_id in self:
            return self[sent_id]
        elif 'default' in kwargs:
            return kwargs['default']
        else:
            raise KeyError("Invalid sentence ID ({})".format(sent_id))

    def _add_sent_obj(self, sent_obj):
        """ [Internal] Add a ttl.Sentence object to this document 
        
        General users should NOT use this function as it is very likely to be removed in the future
        """
        if sent_obj is None:
            raise ValueError("Sentence object cannot be None")
        elif sent_obj.ID is None:
            # if sentID is None, create a new ID
            sent_obj.ID = next(self.__idgen)
        elif sent_obj.ID in self:
            raise ValueError("Sentence ID {} exists".format(sent_obj.ID))
        self.__sent_map[sent_obj.ID] = sent_obj
        self.__sents.append(sent_obj)
        return sent_obj

    def new_sent(self, text, **kwargs):
        """ Create a new sentence and add it to this Document """
        return self._add_sent_obj(Sentence(text, **kwargs))

    def pop(self, sent_ref, **kwargs):
        """ Find and remove a sentence if possible.

        A default keyword argument can be set to return a desired value in case no sentence could be found.
        If no default is provided, KeyError will be raised.

        >>> sent = doc.pop("sent_id_does_not_exist", None)
        >>> sent = doc.pop(sent_obj_from_somewhere_else, None)
        # sent is set to None instead of throwing KeyError

        :param sent_ref: a sentence ID or a sentence object
        """
        sent_id = None
        sent_obj = None
        if sent_ref is None:
            raise ValueError("sent_ref has to be a Sentence object or a Sentence ID")
        elif isinstance(sent_ref, Sentence) and sent_ref.ID and sent_ref.ID in self:
            sent_id = sent_ref.ID
            sent_obj = sent_ref
        elif sent_ref in self:
            sent_id = sent_ref
            sent_obj = self[sent_id]
        # now remove the sentence if possible
        if sent_id is None and not sent_obj is None:
            if 'default' in kwargs:
                return kwargs['default']
            else:
                raise KeyError("Sentence ID {} does not exist".format(sent_ref))
        else:
            # now remove the sentence ...
            self.__sent_map.pop(sent_id)
            self.__sents.remove(sent_obj)
            return sent_obj


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
        sent_path = os.path.join(doc.path, '{}_sents.txt'.format(doc.name))
        token_path = os.path.join(doc.path, '{}_tokens.txt'.format(doc.name))
        concept_path = os.path.join(doc.path, '{}_concepts.txt'.format(doc.name))
        link_path = os.path.join(doc.path, '{}_links.txt'.format(doc.name))
        tag_path = os.path.join(doc.path, '{}_tags.txt'.format(doc.name))

        reader = TxtReader(sent_stream=open(sent_path, mode='rt', encoding=encoding),
                           token_stream=open(token_path, mode='rt', encoding=encoding),
                           concept_stream=open(concept_path, mode='rt', encoding=encoding),
                           link_stream=open(link_path, mode='rt', encoding=encoding),
                           tag_stream=open(tag_path, mode='rt', encoding=encoding),
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
        """ Read tagged doc from mutliple files (sents, tokens, concepts, links, tags) """
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

    STD_DIALECT = 'excel-tab'
    STD_QUOTING = csv.QUOTE_MINIMAL

    def __init__(self, sent_stream, token_stream, concept_stream, link_stream, tag_stream, id_seed=1,
                 csv_dialect=STD_DIALECT, csv_quoting=STD_QUOTING):
        self.sent_stream = sent_stream
        self.token_stream = token_stream
        self.concept_stream = concept_stream
        self.link_stream = link_stream
        self.tag_stream = tag_stream
        self.sent_writer = csv.writer(sent_stream, dialect=csv_dialect, quoting=csv_quoting)
        self.token_writer = csv.writer(token_stream, dialect=csv_dialect, quoting=csv_quoting)
        self.concept_writer = csv.writer(concept_stream, dialect=csv_dialect, quoting=csv_quoting)
        self.link_writer = csv.writer(link_stream, dialect=csv_dialect, quoting=csv_quoting)
        self.tag_writer = csv.writer(tag_stream, dialect=csv_dialect, quoting=csv_quoting)
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
            self.concept_writer.writerow((sid, cid, concept.clemma, concept.value, concept.comment))
            # write cwlinks
            for token in concept.tokens:
                wid = sent.tokens.index(token)
                self.link_writer.writerow((sid, cid, wid))
        # write tags
        for tag in sent.tags:
            self.tag_writer.writerow((sid, tag.cfrom, tag.cto, tag.value, tag.type, ''))
        # write token-level tags
        for wid, token in enumerate(sent.tokens):
            for tag in token:
                self.tag_writer.writerow((sid, tag.cfrom, tag.cto, tag.value, tag.type, wid))

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
        sent_path = os.path.join(doc.path, '{}_sents.txt'.format(doc.name))
        token_path = os.path.join(doc.path, '{}_tokens.txt'.format(doc.name))
        concept_path = os.path.join(doc.path, '{}_concepts.txt'.format(doc.name))
        link_path = os.path.join(doc.path, '{}_links.txt'.format(doc.name))
        tag_path = os.path.join(doc.path, '{}_tags.txt'.format(doc.name))

        return TxtWriter(sent_stream=open(sent_path, mode='wt', encoding=encoding),
                         token_stream=open(token_path, mode='wt', encoding=encoding),
                         concept_stream=open(concept_path, mode='wt', encoding=encoding),
                         link_stream=open(link_path, mode='wt', encoding=encoding),
                         tag_stream=open(tag_path, mode='wt', encoding=encoding), **kwargs)

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
        self.__output_stream.write(json.dumps(sent.to_dict(), ensure_ascii=ensure_ascii))
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
        except Exception:
            logging.getLogger(__name__).exception("Could not close JSONWriter's output stream properly")

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


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def read_json_iter(path):
    """ Iterate through each sentence in a TTL/JSON file """
    if not os.path.isfile(path):
        raise Exception("Document file could not be found: {}".format(path))
    with chio.open(path) as infile:
        for line in infile:
            j = json.loads(line)
            sent = Sentence.from_dict(j)
            yield sent
    return


def read_json(path):
    """ Read a TTL Document in TTL-JSON format """
    if not os.path.isfile(path):
        raise Exception("Document file could not be found: {}".format(path))
    doc_name = os.path.splitext(os.path.basename(path))[0]
    doc_path = os.path.dirname(path)
    doc = Document(doc_name, path=doc_path)
    for sent in read_json_iter(path):
        doc._add_sent_obj(sent)
    return doc


def write_json(path, doc, ensure_ascii=False, **kwargs):
    """ Save a TTL Document in JSON format """
    with JSONWriter.from_path(path) as writer:
        writer.write_doc(doc, ensure_ascii=ensure_ascii, **kwargs)


def read(path, mode=MODE_TSV):
    """ Helper function to read Document in TTL-TXT format (i.e. ${docname}_*.txt)
    E.g. read('~/data/myfile') is the same as Document('myfile', '~/data/').read()
    """
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
    """ Helper function to write doc to TTL-TXT format """
    if mode == MODE_TSV:
        with TxtWriter.from_path(path) as writer:
            writer.write_doc(doc)
    elif mode == MODE_JSON:
        write_json(path, doc, **kwargs)
