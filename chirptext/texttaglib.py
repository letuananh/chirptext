# -*- coding: utf-8 -*-

""" Text Annotation (texttaglib - TTL) module
"""

# This code is a part of chirptext library: https://github.com/letuananh/chirptext
# :copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import csv
import json
import logging
import os
from collections import Mapping
from collections import defaultdict as dd
from typing import TypeVar, Generic

from . import chio
from .anhxa import DataObject
from .anhxa import IDGenerator
from .chio import iter_tsv_stream

MODE_TSV = 'tsv'
MODE_JSON = 'json'


class Tag(DataObject):

    """ A general tag which can be used for annotating linguistic objects such as Sentence, Chunk, or Token

    Note: object types cannot be None. If forced with ``Tag('val', type=None)`` type will be set to an empty string ''
    If an object is passed in as type str(type) will be used to convert it into a string.
    """
    GOLD = 'gold'
    NONE = ''
    DEFAULT = 'n/a'
    MFS = 'mfs'  # most frequent sense
    WORDNET = 'wn'
    OTHER = 'other'
    NLTK = 'nltk'
    ISF = 'isf'  # integrated semantic framework: https://github.com/letuananh/intsem.fx
    MECAB = "mecab"

    def __init__(self, value: str = '', type: str = NONE, cfrom=-1, cto=-1, source=NONE, **kwargs):
        super().__init__(**kwargs)
        self.__value = value if value == '' or value is None else str(value)
        self.__type = str(type) if type else ''  # tag type
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
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        self.__value = value

    @property
    def type(self):
        return self.__type

    @property
    def cto(self):
        """ ending character index of a Tag """
        return self.__cto

    @cto.setter
    def cto(self, value):
        self.__cto = int(value) if value is not None else None

    @property
    def text(self):
        """ The text value of this tag

        Tag.text returns Tag.value except when value does not exist (i.e. is None)
        in which an empty string '' will be returned
        """
        return self.value if self.value else ''

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
            return f"{self.type}/{self.value}[{self.cfrom}:{self.cto}]"
        else:
            return f"{self.type}/{self.value}"

    def to_dict(self, default_cfrom=-1, default_cto=-1, *args, **kwargs):
        """ Serialize this Tag object data into a dict """
        a_dict = {'value': self.value}
        if self.type:
            a_dict['type'] = self.type
        if self.source:
            a_dict['source'] = self.source
        if self.cfrom not in (None, -1, default_cfrom, self.parent.cfrom if self.parent else None) and self.cfrom >= 0:
            a_dict['cfrom'] = self.cfrom
        if self.cto not in (None, -1, default_cto, self.parent.cto if self.parent else None) and self.cto >= 0:
            a_dict['cto'] = self.cto
        return a_dict

    def clone(self, **kwargs):
        """ Create a new tag object """
        _source_dict = self.to_dict()
        _source_dict.update(kwargs)
        return Tag.from_dict(_source_dict)

    @staticmethod
    def from_dict(json_dict):
        """ Create a Tag object from a dict's data """
        tag = Tag(**json_dict)
        return tag


T = TypeVar('TagType')


class ProtoList:

    """ A list of data objects that can construct new children """

    def __init__(self, parent=None, proto=Tag, proto_kwargs=None, proto_key="ID", index_key=False,
                 claim_hook=None, release_hook=None, taglist_create_hook=None, *args, **kwargs):
        self.__parent = parent
        self.__proto = proto
        self.__proto_kwargs = proto_kwargs
        self.__proto_key = proto_key
        self.__obj_map = {}
        self.__has_index = index_key and proto_key
        self.__claim_hook = claim_hook  # notify parent to claim an object
        self.__release_hook = release_hook  # notify parent that an object has been removed
        self.__taglist_create_hook = taglist_create_hook  # notify parent that TagList created a new object using new()
        self.__children = []

    def __len__(self):
        return len(self.__children)

    def __iter__(self):
        return iter(self.__children)

    def __getitem__(self, idx):
        if isinstance(idx, int):
            return self.__children[idx]
        elif self.__has_index:
            return self.__obj_map[idx]
        else:
            raise IndexError("object search value has to be either sequence position (int) or key (str)")

    def __setitem__(self, key, value):
        return self._add_obj(value, key, replace=True)

    def __contains__(self, value):
        if self.__has_index:
            return value in self.__children or value in self.__obj_map
        else:
            return value in self.__children

    def __repr__(self):
        return repr([repr(c) for c in self])
        
    def __str__(self):
        return str([str(c) for c in self])

    def new(self, *args, **kwargs):
        """ Create a new object and add this this TokenList """
        # prefer kwargs to proto_kwargs, except for type
        if self.__proto_kwargs:
            for k, v in self.__proto_kwargs.items():
                if k == 'type':
                    if 'type' in kwargs and kwargs['type']:
                        if kwargs['type'] != self.__proto_kwargs['type']:
                            raise ValueError("Cannot construct new object due to conflicting types")
                    kwargs['type'] = self.__proto_kwargs['type']
                elif k not in kwargs:
                    kwargs[k] = self.__proto_kwargs[k]
        new_obj = self.__proto(*args, **kwargs)
        if self.__taglist_create_hook:
            self.__taglist_create_hook(new_obj)
        return self._add_obj(new_obj)

    def append(self, obj):
        return self._add_obj(obj)

    def extend(self, values):
        for obj in values:
            self.append(obj)

    def insert(self, idx, obj):
        self._add_obj(obj, idx=idx)

    def index(self, *args, **kwargs):
        return self.__children.index(*args, **kwargs)

    def _add_obj(self, obj, idx=None, replace=False):
        """ [Internal function] Add an existing object into this list

        Currently this function is only used for constructing structures from input streams.
        General users should NOT use this function as it is very likely to be removed in the future

        :param obj: a new object to add to this list
        :param idx: position to insert the new object to, or set to None to append the new object to the end of list.
        :param replace: replace an existing object at a given position instead of inserting
        """
        if self.__claim_hook:
            self.__claim_hook(obj)
        if self.__has_index:
            if getattr(obj, self.__proto_key):
                self.__obj_map[getattr(obj, self.__proto_key)] = obj
        if idx is None:
            self.__children.append(obj)
        elif replace:
            _old_obj = self.__children[idx]
            self._release_obj(_old_obj)
            self.__children[idx] = obj
        else:
            self.__children.insert(idx, obj)
        return obj

    def by_id(self, id: str, **kwargs):
        """ ID value has to be string """
        for _obj in self:
            if getattr(_obj, self.__proto_key) == id:
                return _obj
        if 'default' in kwargs:
            return kwargs['default']
        else:
            raise IndexError("No object could be found with the given index and no default value was provided")

    def remove(self, obj_ref):
        # remove from map
        if obj_ref in self.__obj_map:
            _obj = self.__obj_map[obj_ref]
        else:
            _obj = obj_ref
        # remove the object from this list
        if _obj in self.__children:
            self.__children.remove(_obj)
        return self._release_obj(_obj)

    def _release_obj(self, obj):
        # remove the obj from obj map index
        if self.__has_index:
            key = getattr(obj, self.__proto_key)
            self.__obj_map.pop(key)
        if self.__release_hook:
            self.__release_hook(obj)
        return obj

    def values(self):
        """ Compile a value list from all children """
        return [c.value for c in self.__children]


class TagSet(Generic[T]):
    """ contains all tags of a linguistic object """

    class TagMap:
        def __init__(self, tagset):
            self.__dict__["_TagMap__tagset"]: TagSet = tagset

        def __getitem__(self, type) -> T:
            """ Get the first tag object in the tag list of a given type if exist, else return None """
            if type in self.__tagset and len(self.__tagset[type]) > 0:
                return self.__tagset[type][0]
            else:
                return None

        def __setitem__(self, type, value):
            """ Set the first tag object in the tag list of a given type to key if exist, else create a new tag

            :param type: type of the generic tag object being added
            :param value: if value is a dict-like object, it will be unpacked into object constructor, otherwise it will be used as the tag value
            """
            _old = self[type]
            _kwargs = {}
            if isinstance(value, Mapping):
                _kwargs = value
                if 'type' in _kwargs:
                    if _kwargs['type'] != type:
                        raise ValueError("Multiple values for type were provided")
                    else:
                        _kwargs.pop('type')
                value = _kwargs.pop('value') if 'value' in _kwargs else ''
            if not _old:
                # create a new tag
                self.__tagset.new(value, type=type, **_kwargs)
            else:
                # pop the old tag and replace it with a new one
                self.__tagset.replace(_old, value, type=type, **_kwargs)

        def __getattr__(self, type) -> T:
            """ get the first tag object in the tag list of a given type if exist, else return None """
            return self[type]

        def __setattr__(self, type, value):
            """ Set the first tag object in the tag list of a given type to key if exist, else create a new tag """
            self[type] = value

        def get_or_create(self, type, default=None, check_type=True):
            """ Get an existing tag object with a specific type, or create a new one using defaulted values

            :param default: A Tag object or a dict-like structure, both will be used to construct a new Tag object
                             If defaults is set to None then an empty tag of the given type will be created
            :param check_type: Make sure that type information in defaults is not conflicting with querying type
            :raises: ValueError
            """
            if type in self.__tagset:
                return self[type]
            elif default is None:
                return self.__tagset.new('', type=type)
            elif isinstance(default, Tag):
                if check_type and default.type and default.type != type:
                    raise ValueError(
                        f"Could not create new tag object due to type conflicting ({repr(type)} != {repr(default.type)})")
                else:
                    return self.__tagset._append(default.clone(type=type))
            elif isinstance(default, Mapping):
                _kwargs = dict(default)
                if 'value' in _kwargs:
                    _value = _kwargs.pop("value")
                else:
                    _value = None
                if 'type' in _kwargs:
                    if check_type and _kwargs['type'] != type:
                        raise ValueError(
                            f"Could not create new tag object due to type conflicting ({repr(type)} != {repr(_kwargs['type'])})")
                    _kwargs.pop("type")
                    return self.__tagset.new(_value, type=type, **_kwargs)
            else:
                # use defaults as the input value string
                return self.__tagset.new(str(default), type=type)

    def __init__(self, parent=None, **kwargs):
        self.__parent = parent
        self.__proto_kwargs = kwargs['proto_kwargs'] if 'proto_kwargs' in kwargs else {}
        self.__proto = kwargs['proto'] if 'proto' in kwargs else Tag
        self.__dict__["_TagSet__tags"] = []
        self.__dict__["_TagSet__tagmap"] = TagSet.TagMap(self)
        self.__dict__["_TagSet__tagsmap"] = dict()

    @property
    def gold(self):
        """ Interact with first tag (gold) directly """
        return self.__tagmap

    def __len__(self):
        """ Number of tags in this object """
        return len(self.__tags)

    def __getitem__(self, type) -> T:
        """ Get the all tags of a given type """
        if type not in self.__tagsmap:
            self.__tagsmap[type] = ProtoList(proto=self.__proto,
                                             proto_kwargs={'type': type},
                                             taglist_create_hook=lambda x: self.__tags.append(x))
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

    def _construct_obj(self, *args, **kwargs) -> T:
        """ Construct a new tag object and notify parent if possible """
        if self.__proto_kwargs:
            # prioritise values in kwargs rather than in default constructor kwargs
            for k, v in self.__proto_kwargs.items():
                if k not in self.kwargs:
                    kwargs[k] = v
        _tag = self.__proto(*args, **kwargs)
        # TODO to review this _claim book design
        if self.__parent is not None and self.__parent._claim:
            self.__parent._claim(_tag)
        return _tag

    def new(self, value, type='', *args, **kwargs) -> T:
        """ Create a new generic tag object """
        if not value and not type:
            raise ValueError("Concept value and type cannot be both empty")
        _tag = self._construct_obj(value, type, *args, **kwargs)
        return self._append(_tag)

    def _append(self, tag):
        """ [Internal] Add an existing tag object into the list

        General users should NOT use this method as it is very likely to be removed in the future
        """
        self.__map_tag(tag)
        self.__tags.append(tag)
        return tag

    def __map_tag(self, tag):
        self[tag.type].append(tag)
        return tag

    def _replace_obj(self, old_obj, new_obj):
        self.__tags.remove(old_obj)
        self.__tags.append(new_obj)
        if old_obj.type == new_obj.type:
            _taglist = self.__tagsmap[old_obj.type]
            _taglist[_taglist.index(old_obj)] = new_obj
        else:
            self.__tagsmap[old_obj.type].remove(old_obj)
            self.__tagsmap[new_obj.type].append(new_obj)
        return new_obj

    def replace(self, old_obj, value: str, type='', *args, **kwargs) -> T:
        """ Create a new tag to replace an existing tag object

        :param old_obj: Old object to be removed and replaced with a newly crated object
        :param value: text value for the new tag object
        :param type: type for the new object, defaulted to an empty string
        """
        new_obj = self._construct_obj(value=value, type=type, *args, **kwargs)
        return self._replace_obj(old_obj, new_obj)

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
        """ Remove a tag at a given position and return it """
        return self.remove(self.__tags[idx])

    def index(self, obj):
        return self.__tags.index(obj)

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
        self.__text = text  # original/surface form
        self.lemma = lemma   # dictionary form
        self.pos = pos
        self.comment = comment
        self.flag = flag

    def __getitem__(self, name):
        return self.tag[name].value if name in self.__tags else None

    def __setitem__(self, name, value):
        self.tag[name] = value

    def __getattr__(self, name):
        return self[name]

    def __len__(self):
        return len(self.__tags)

    def __iter__(self):
        return iter(self.__tags)

    def __repr__(self):
        return "`{l}`<{f}:{t}>".format(l=self.text, f=self.cfrom, t=self.cto)

    def __str__(self):
        return self.text

    @property
    def text(self):
        """ Text value of a Token object """
        return self.__text

    @text.setter
    def text(self, value):
        self.__text = value

    @property
    def value(self):
        """ Alias to Token.text """
        return self.text

    @value.setter
    def value(self, value):
        self.text = value

    @property
    def tag(self):
        return self.__tags.gold

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

    def tag_map(self):
        """ Build a map from tagtype to list of tags """
        tm = dd(list)
        for tag in self.__tags:
            tm[tag.type].append(tag)
        return tm

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
            tk.tags.new(**tag_json)
        return tk


class TokenList(list):
    """ A list of Token - Accept both token index and token object """
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.sent = None

    def __eq__(self, other):
        if not isinstance(other, list):
            return False
        elif len(other) != len(self):
            return False
        else:
            for i1, i2 in zip(self, other):
                if i1 != i2:
                    return False
            return True

    def __add__(self, other):
        return self.extend(other)

    def __iadd__(self, other):
        return self.extend(other)

    def __ensure_token(self, token):
        if isinstance(token, Token):
            return token
        elif isinstance(token, int):
            if self.sent is None:
                raise ValueError("Using token index in a TokenList without sentence ref")
            return self.sent[token]
        else:
            raise ValueError(f"Invalid token value: {token} (Only token index and Token objects are accepted")

    def append(self, x):
        """ Add tokens to this concept """
        super().append(self.__ensure_token(x))

    def extend(self, iterable):
        """ Add all tokens from an iterable to this TokenList

        :param iterable: An iterable of int (for token indices) or Token list
        :raises: ValueError
        """
        super().extend(self.__ensure_token(t) for t in iterable)

    def insert(self, i, x):
        """ Insert a token at a given position """
        super().insert(i, self.__ensure_token(x))


class Concept(Tag):

    """ Represent a concept in an utterance, which may refers to multiple tokens """

    FLAG = 'flag'
    COMMENT = 'comment'
    NOT_MATCHED = 'E'

    def __init__(self, value='', type=None, clemma=None, tokens=None, comment=None, flag=None, sent=None, **kwargs):
        super().__init__(value, type, **kwargs)
        self.__tokens = TokenList()
        self.sent = sent
        self.clemma = clemma
        if tokens:
            self.tokens.extend(tokens)
        self.comment = comment
        self.flag = flag

    @property
    def tokens(self):
        return self.__tokens

    @tokens.setter
    def tokens(self, values):
        self.__tokens.clear()
        self.__tokens.extend(values)

    @property
    def sent(self):
        return self.__sent

    @sent.setter
    def sent(self, value):
        self.__sent = value
        self.__tokens.sent = value

    def __getitem__(self, idx):
        """ Get the idx-th token of this concept """
        return self.__tokens[idx]

    def __iter__(self):
        """ Iterate through all tokens in this concept """
        return iter(self.__tokens)

    def __len__(self):
        """ Number of tokens belong to this concept """
        return len(self.__tokens)

    def __repr__(self):
        return f'<{self.type}:{self.value}:"{self.clemma}">'

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
        if self.value:
            concept_dict['value'] = self.value
        if self.type:
            concept_dict['type'] = self.type
        if self.comment:
            concept_dict[Concept.COMMENT] = self.comment
        if self.flag:
            concept_dict[Concept.FLAG] = self.flag
        return concept_dict


class Sentence(DataObject):

    """ Represent an utterance (i.e. a sentence) """

    def __init__(self, text='', ID=None, tokens=None, **kwargs):
        super().__init__(text=text, **kwargs)
        self.text = text
        self.ID = ID
        self.__tags: TagSet[Tag] = TagSet[Tag](parent=self)
        self.__concepts: TagSet[Concept] = TagSet[Concept](proto=Concept, proto_kwargs={'sent': self})
        self.__tokens: ProtoList = ProtoList(parent=self, proto=Token, proto_kwargs={'sent': self})
        if tokens:
            self.tokens = tokens

    @property
    def ID(self) -> str:
        """ ID string of a sentence """
        return self.__ID

    @ID.setter
    def ID(self, value: str):
        self.__ID = str(value) if value is not None else None

    @property
    def text(self):
        return self.__text

    @text.setter
    def text(self, value):
        self.__text = value

    def __repr__(self):
        if self.ID:
            return f"Sentence(ID={repr(self.ID)}, text={repr(self.text)})"
        else:
            return f"Sentence({repr(self.text)})"

    def __str__(self):
        """ The text content of this sentence """
        return self.text

    def __getitem__(self, idx: int) -> Token:
        """ Get the token at a given position in this sentence """
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
            self.tokens.new(token, cfrom, cto)
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
            sent.tokens._add_obj(Token.from_dict(json_token))
        # import concepts
        for json_concept in json_sent.get('concepts', []):
            concept = sent.concepts.new(**json_concept)
            concept.update(json_concept, Concept.COMMENT, Concept.FLAG)
        # import sentence's tag
        for json_tag in json_sent.get('tags', []):
            sent.tags.new(**json_tag)
        return sent


class Document(DataObject):

    def __init__(self, name='', path='.', **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.path = path
        self.__sents = ProtoList(parent=self, proto=Sentence, index_key=True, claim_hook=self.__claim_sent_obj)
        self.__idgen = IDGenerator(id_hook=lambda x: x in self)  # for creating a new sentence without ID

    @property
    def sents(self):
        return self.__sents

    def __contains__(self, sent_id):
        """ Check if a given sentence ID exists in this Document """
        return str(sent_id) in self.__sents

    def __len__(self):
        return len(self.__sents)

    def __getitem__(self, sent_ref) -> Sentence:
        """ Get a sentence object by ID (string) or position (int) """
        return self.__sents[sent_ref]

    def __iter__(self):
        """ Return an iterator to loop though all sentences in this Document """
        return iter(self.__sents)

    def __claim_sent_obj(self, sent: Sentence):
        if not sent.ID:
            sent.ID = next(self.__idgen)


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
                doc.sents.new(text.strip(), ID=sid)
            elif len(row) == 4:
                sid, text, flag, comment = row
                sent = doc.sents.new(text.strip(), ID=sid)
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
                sent_tokens_map[sid].append((token, lemma, pos.strip(), wid, comment))
            # import tokens
            for sent in doc:
                sent_tokens = sent_tokens_map[sent.ID]
                sent.tokens = ([x[0] for x in sent_tokens])
                for ((tk, lemma, pos, wid, comment), token) in zip(sent_tokens, sent.tokens):
                    token.pos = pos
                    token.lemma = lemma
                    token.comment = comment
            # only read concepts if tokens are available
            if self.concept_stream:
                concept_map = {}
                # read concepts
                for concept_row in self.concept_reader():
                    if len(concept_row) == 6:
                        sid, cid, clemma, value, _type, comment = concept_row
                    elif len(concept_row) == 5:
                        sid, cid, clemma, value, _type = concept_row
                    else:
                        sid, cid, clemma, value = concept_row
                        comment = ''
                        _type = ''
                    if not value and not _type:
                        raise ValueError("Invalid concept line (concept value and type cannot be both zero)")
                    cid = int(cid)
                    sent = doc[sid]
                    # TODO: read type info from file
                    c = sent.concepts.new(value.strip(), type=_type, clemma=clemma, comment=comment)
                    concept_map[(sid, cid)] = c
                # only read concept-token links if tokens and concepts are available
                for sid, cid, wid in self.link_reader():
                    sent = doc[sid]
                    concept = concept_map[(sid, int(cid.strip()))]
                    token = sent[int(wid.strip())]
                    concept.tokens.append(token)
        # read sentence level tags
        if self.tag_stream:
            for row in self.tag_reader():
                if len(row) == 5:
                    sid, cfrom, cto, value, _type = row
                    wid = None
                if len(row) == 6:
                    sid, cfrom, cto, value, _type, wid = row
                if cfrom:
                    cfrom = int(cfrom)
                if cto:
                    cto = int(cto)
                if wid is None or wid == '':
                    doc[sid].tags.new(value=value, type=_type, cfrom=cfrom, cto=cto)
                else:
                    doc[sid][int(wid)].tags.new(value=value, type=_type, cfrom=cfrom, cto=cto)
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
            self.concept_writer.writerow((sid, cid, concept.clemma, concept.value, concept.type, concept.comment))
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
