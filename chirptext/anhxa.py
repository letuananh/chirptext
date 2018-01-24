# -*- coding: utf-8 -*-

'''
Data mapping functions
Latest version can be found at https://github.com/letuananh/chirptext

References:
    Python documentation:
        https://docs.python.org/
    PEP 0008 - Style Guide for Python Code
        https://www.python.org/dev/peps/pep-0008/
    PEP 257 - Python Docstring Conventions:
        https://www.python.org/dev/peps/pep-0257/

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

import logging
import json
from json import JSONDecoder, JSONEncoder


# -------------------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------------------

def getLogger():
    return logging.getLogger(__name__)


# -------------------------------------------------------------------------------
# FUNCTIONS
# -------------------------------------------------------------------------------

def field(f, field_map):
    return f if f not in field_map else field_map[f]


def dumps(obj, *args, **kwargs):
    ''' Typeless dump an object to json '''
    return json.dumps(obj, *args, cls=TypelessSONEncoder, **kwargs)


def update_obj(source, target, *fields, **field_map):
    source_dict = source.__dict__ if hasattr(source, '__dict__') else source
    if not fields:
        fields = source_dict.keys()
    for f in fields:
        target_f = f if f not in field_map else field_map[f]
        setattr(target, target_f, source_dict[f])


def to_json(obj, *fields, **field_map):
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
