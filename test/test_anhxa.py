#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Test script for anhxa
Latest version can be found at https://github.com/letuananh/chirptext

:copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
:license: MIT, see LICENSE for more details.
'''

import os
import unittest
import json
import logging
from chirptext.anhxa import IDGenerator, DataObject
from chirptext.anhxa import to_dict, to_obj, dumps, update_obj
from chirptext.anhxa import TypedJSONDecoder, TypelessSONEncoder, TypedJSONEncoder


# -------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------

TEST_DIR = os.path.dirname(os.path.realpath(__file__))


def getLogger():
    return logging.getLogger(__name__)


# -------------------------------------------------------------------------------
# Data Structures
# -------------------------------------------------------------------------------

class PersonifyJSONEncoder(TypedJSONEncoder):

    def __init__(self, *args, **kwargs):
        type_map = {Person: '__person__',
                    Job: '__job__'}
        super(PersonifyJSONEncoder, self).__init__(type_map=type_map, *args, **kwargs)


class PersonifyJSONDecoder(TypedJSONDecoder):

    def __init__(self, *args, **kwargs):
        type_map = {'__person__': Person,
                    '__job__': Job}
        super(PersonifyJSONDecoder, self).__init__(type_map)


class Job(object):

    def __init__(self, job='N/A', sal=0):
        self.job = job
        self.sal = sal

    def __str__(self):
        return ("{} (${}/mth)".format(self.job, self.sal))

    def __eq__(self, other):
        if not other:
            return False
        else:
            return self.job == other.job and self.sal == other.sal


class Person(object):

    def __init__(self, name='', age='', job=None, pid=None):
        self.name = name
        self.age = age
        self.job = job if job else None
        self.pid = pid

    def change_job(self, job, sal):
        self.job = Job(job, sal)

    def __str__(self):
        return "{} ({}) {}".format(self.name, self.age, self.job if self.job else 'unemployed')

    def __eq__(self, other):
        if not other:
            return False
        return self.name == other.name and self.age == other.age and self.job == other.job


# -------------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------------

class TestIDGen(unittest.TestCase):

    def no_even(self, value):
        if value > 0 and value % 2 == 0:
            return True

    def test_idgen(self):
        gen = IDGenerator(id_hook=self.no_even)
        ids = [next(gen) for i in range(5)]
        self.assertEqual(ids, [1, 3, 5, 7, 9])
        # test no hook
        gen2 = IDGenerator()
        ids = [next(gen2) for i in range(5)]
        self.assertEqual(ids, [1, 2, 3, 4, 5])


class TestDataObject(unittest.TestCase):

    def test_dobj(self):
        desc = 'Just an ordinary foo'
        source = {'name': 'foo', 'age': 18, 'desc': desc, 'silent': False}
        obj = DataObject(funny=True)
        obj.hobbies = {'coding', 'languages'}
        obj.update(source, desc='description', silent='muet')
        obj.update(source, 'nonexistence')  # this is OK too
        self.assertEqual(obj.name, 'foo')
        self.assertEqual(obj.age, 18)
        self.assertEqual(obj.description, desc)
        self.assertFalse(obj.muet)
        oj = obj.to_json()
        self.assertNotIn('nonexistence', oj)
        getLogger().debug(oj)


class TestAnhxa(unittest.TestCase):

    def test_new_object(self):
        p = to_obj(Person, {'name': 'Ji', 'age': 10, 'pid': 'p001'})
        p.job = 'dev'
        pj = to_dict(p)
        p2 = to_obj(Person, pj)
        self.assertIsInstance(p2, Person)
        self.assertEqual(p, p2)
        #
        pj2 = to_dict(pj, 'name', 'age', 'pid')
        p3 = to_obj(Person, pj2)
        self.assertFalse(p3.job)
        # obj to obj
        p4 = to_obj(Person, p3.__dict__)
        self.assertEqual(p3, p4)

    def test_json_encoder(self):
        p = to_obj(Person, {'name': 'Ji', 'age': 10})
        # Person > typed-json
        js = json.dumps(p, cls=PersonifyJSONEncoder)
        # typed-json > Person
        np = json.loads(js, cls=PersonifyJSONDecoder)
        self.assertIsInstance(np, Person)
        npjson = json.dumps(np, cls=PersonifyJSONEncoder)
        self.assertEqual(npjson, js)
        #
        # changing info
        p.change_job('dev', 5000)
        js2 = json.dumps(p, cls=PersonifyJSONEncoder)
        # change salary in JSON
        js2_json = json.loads(js2)
        js2_json['job']['sal'] = 10000
        # convert js2_json to object
        np2 = json.loads(json.dumps(js2_json), cls=PersonifyJSONDecoder)
        self.assertEqual(np2.job.sal, 10000)

    def test_typeless_json(self):
        p = to_obj(Person, {'name': 'Chun', 'age': 15})
        p.change_job('pupil', -500)
        pjstr = json.dumps(p, cls=PersonifyJSONEncoder)
        pjson = json.loads(pjstr)
        self.assertIn('__type__', pjson)
        self.assertEqual(pjson['__type__'], '__person__')
        self.assertIn('__type__', pjson['job'])
        self.assertEqual(pjson['job']['__type__'], '__job__')

        # Test typeless json
        # helper function
        pjtl = dumps(p, indent=2)
        pjson1 = json.loads(pjtl)
        # or full method
        pjtl2 = json.dumps(p, cls=TypelessSONEncoder)
        pjson2 = json.loads(pjtl2)
        self.assertEqual(pjson1, pjson2)

    def test_mapping(self):
        p1 = to_obj(Person, {'name': 'Yin', 'age': 10, 'pid': '001'})
        p2 = to_obj(Person, {'name': 'Yang', 'age': 5, 'pid': '002'})
        p2.job = Job("pupil", -100)
        # p2 > json
        p2json = json.loads(dumps(p2))
        update_obj(p2json, p1, 'name', 'age', 'pid')
        p1.job = to_obj(Job, p2json['job'])
        self.assertEqual(p1, p2)
        # now change p1 salary
        p1.job.sal = -200
        self.assertNotEqual(p1.job.sal, p2.job.sal)

    def test_different_key_mapping(self):
        p1 = to_obj(Person, {'name': 'Yin', 'age': 10, 'pid': '001'})
        o2j_map = {'pid': 'perid'}
        j2o_map = {v: k for k, v in o2j_map.items()}
        p1j = to_dict(p1, **o2j_map)
        p2 = to_obj(Person, p1j, **j2o_map)
        self.assertEqual(p1, p2)


# -------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()
