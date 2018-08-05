# -*- coding: utf-8 -*-

'''
Data mapping functions
Latest version can be found at https://github.com/letuananh/chirptext

:copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
:license: MIT, see LICENSE for more details.
'''

import logging
import threading
import json
from json import JSONDecoder, JSONEncoder


# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

def getLogger():
    return logging.getLogger(__name__)


# -------------------------------------------------------------------------------
# Functions
# -------------------------------------------------------------------------------

class IDGenerator(object):

    def __init__(self, id_seed=1, id_hook=None):
        ''' id_seed = starting number '''
        self.__id_seed = id_seed
        self.__id_check_hook = id_hook  # external ID checker
        self.__lock = threading.Lock()

    def __next__(self):
        with self.__lock:
            while True:
                valid_id = self.__id_seed
                self.__id_seed += 1
                if self.__id_check_hook is None or not self.__id_check_hook(valid_id):
                    break
            return valid_id


class DataObject(object):

    def __init__(self, **kwargs):
        self.__extra_data = {}  # for internal purpose
        add_extra_fields(self, kwargs)

    def __getattr__(self, attr_name):
        return self.__extra_data[attr_name] if attr_name in self.__extra_data else None

    def update(self, a_dict, *fields, **field_map):
        flex_update_obj(a_dict, self, True, *fields, **field_map)

    def to_json(self, *args, **kwargs):
        return dumps(self, *args, **kwargs)

    def to_dict(self, *args, **kwargs):
        a_dict = to_json(self)
        if '_DataObject__extra_data' in a_dict and not a_dict['_DataObject__extra_data']:
            a_dict.pop('_DataObject__extra_data')
        return a_dict


def field(f, field_map):
    return f if f not in field_map else field_map[f]


def add_extra_fields(obj, kwargs):
    for k, v in kwargs.items():
        if k not in obj.__dict__:
            obj.__dict__[k] = v
        else:
            raise Exception("Attribute {} exists".format(k))


def dumps(obj, *args, **kwargs):
    ''' Typeless dump an object to json string '''
    return json.dumps(obj, *args, cls=TypelessSONEncoder, ensure_ascii=False, **kwargs)


def update_obj(source, target, *fields, **field_map):
    flex_update_obj(source, target, False, *fields, **field_map)


def flex_update_obj(source, target, __silent, *fields, **field_map):
    ''' Pull data from source to target.
    Target's __dict__ (object data) will be used by default. Otherwise, it'll be treated as a dictionary '''
    source_dict = source.__dict__ if hasattr(source, '__dict__') else source
    if not fields:
        fields = source_dict.keys()
    for f in fields:
        if f not in source_dict and __silent:
            continue
        target_f = f if f not in field_map else field_map[f]
        setattr(target, target_f, source_dict[f])


def to_json(obj, *fields, **field_map):
    if isinstance(obj, set):
        return list(obj)
    obj_dict = obj.__dict__ if hasattr(obj, '__dict__') else obj
    if not fields:
        fields = obj_dict.keys()
    json_dict = {field(k, field_map): obj_dict[k] for k in fields}
    return json_dict


def to_obj(cls, obj_data=None, *fields, **field_map):
    ''' Use obj_data (dict-like) to construct an object of type cls
    prioritize obj_dict when there are conficts '''
    if not fields:
        fields = obj_data.keys()
    try:
        kwargs = {field(f, field_map): obj_data[f] for f in fields if f in obj_data}
        obj = cls(**kwargs)
    except:
        getLogger().exception("Couldn't use kwargs to construct object")
        # use default constructor
        obj = cls()
        update_obj(obj_data, obj, *fields, **field_map)
    return obj


class TypedJSONEncoder(JSONEncoder):

    def __init__(self, *args, type_map=None, **kwargs):
        JSONEncoder.__init__(self, *args, **kwargs)
        self.type_map = type_map if type_map else {}

    def default(self, obj):
        if obj.__class__ in self.type_map:
            nj = to_json(obj)
            nj['__type__'] = self.type_map[obj.__class__]
            return nj
        else:
            return JSONEncoder.default(self, obj)


class TypelessSONEncoder(JSONEncoder):

    def __init__(self, *args, type_map=None, **kwargs):
        JSONEncoder.__init__(self, *args, **kwargs)
        self.type_map = type_map if type_map else {}

    def default(self, obj):
        try:
            return JSONEncoder.default(self, obj)
        except TypeError:
            # fall back to to_json helper function
            return to_json(obj)


class TypedJSONDecoder(JSONDecoder):

    def __init__(self, type_map=None, **kwargs):
            JSONDecoder.__init__(self, object_hook=self.obj_hooker)
            self.type_map = kwargs
            if type_map:
                self.type_map.update(type_map)

    def obj_hooker(self, obj_dict):
        if '__type__' in obj_dict:
            # check if this type is supported
            if obj_dict['__type__'] in self.type_map:
                obj_type = obj_dict.pop('__type__')
                return to_obj(self.type_map[obj_type], obj_dict)
            else:
                getLogger().warning("Unknown type: {}".format(obj_dict['__type__']))
        else:
            return obj_dict
