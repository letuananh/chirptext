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
'''

# Copyright (c) 2017, Le Tuan Anh <tuananh.ke@gmail.com>
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

__author__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__copyright__ = "Copyright 2017, chirptext"
__license__ = "MIT"
__maintainer__ = "Le Tuan Anh"
__version__ = "0.1"
__status__ = "Prototype"
__credits__ = []

########################################################################

import logging
import json
from json import JSONDecoder, JSONEncoder


#-------------------------------------------------------------------------------
# CONFIGURATION
#-------------------------------------------------------------------------------


#-------------------------------------------------------------------------------
# FUNCTIONS
#-------------------------------------------------------------------------------

def dumps(obj, *args, **kwargs):
    ''' Typeless dump an object to json '''
    return json.dumps(obj, *args, cls=TypelessSONEncoder, **kwargs)


def update_data(source, target, *fields, **field_map):
    source_dict = source.__dict__ if hasattr(source, '__dict__') else source
    target_dict = target.__dict__ if hasattr(target, '__dict__') else target
    if not fields:
        fields = source_dict.keys()
    for f in fields:
        target_f = f if f not in field_map else field_map[f]
        target_dict[target_f] = source_dict[f]


def to_json(obj, *fields, **field_map):
    obj_dict = obj.__dict__ if hasattr(obj, '__dict__') else obj
    if not fields:
        fields = obj_dict.keys()
    json_dict = {(k if k not in field_map else field_map[k]): obj_dict[k] for k in fields}
    return json_dict


def to_obj(cls, obj_data=None, *fields, **field_map):
    ''' prioritize obj_dict when there are conficts '''
    obj_dict = obj_data.__dict__ if hasattr(obj_data, '__dict__') else obj_data
    if not fields:
        fields = obj_dict.keys()
    obj_kwargs = {}
    for k in fields:
        f = k if k not in field_map else field_map[k]
        obj_kwargs[f] = obj_dict[k]
    obj = cls(**obj_kwargs)
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
                logging.warning("Unknown type: {}".format(obj_dict['__type__']))
        else:
            return obj_dict
