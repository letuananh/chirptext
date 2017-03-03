#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Chirptext Arsenal - Cache utilities

Latest version can be found at https://github.com/letuananh/chirptext
References:
    Python documentation:
        https://docs.python.org/
    PEP 0008 - Style Guide for Python Code
        https://www.python.org/dev/peps/pep-0008/
    PEP 0257 - Python Docstring Conventions:
        https://www.python.org/dev/peps/pep-0257/
'''

#Copyright (c) 2017, Le Tuan Anh <tuananh.ke@gmail.com>

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

__author__ = "Le Tuan Anh <tuananh.ke@gmail.com>"
__copyright__ = "Copyright 2017, chirptext"
__credits__ = ["Le Tuan Anh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

#-----------------------------------------------------------------------------

import os
import uuid
import logging
import sqlite3
import zlib

from .leutile import FileHelper


# TODO: Use puchikarui for better DB access
class JiCache:
    ''' Cache textual/binary content using an SQLite file (with internal blob or an external folder)
    '''
    def __init__(self, location, blob_location=None, use_internal_blob=False):
        self.location = os.path.abspath(os.path.expanduser(location))
        self.blob_location = os.path.abspath(os.path.expanduser(blob_location)) if blob_location else self.location + '.blob'
        self.use_internal_blob = use_internal_blob
        logging.getLogger().info("Cache DB location    : {location}".format(location=self.location))
        logging.getLogger().info("Blob location        : {blob_loc}".format(blob_loc=self.blob_location))
        logging.getLogger().info("Store BLOB internally: {storage_mode}".format(storage_mode=self.use_internal_blob))
        self.setup()

    def setup(self):
        if not self.use_internal_blob:
            FileHelper.createIfNeeded(self.blob_location)
        conn = None
        try:
            conn = sqlite3.connect(self.location)
            c = conn.cursor()
            # Create tables
            c.execute('''CREATE TABLE IF NOT EXISTS cache_entries (key UNIQUE, value);''')
            c.execute("""CREATE INDEX IF NOT EXISTS CACHE_ENTRIES_KEY_INDEX ON cache_entries (key);""")
            c.execute('''CREATE TABLE IF NOT EXISTS blob_entries (key UNIQUE, compressed, blob_data);''')
            c.execute("""CREATE INDEX IF NOT EXISTS BLOB_ENTRIES_KEY_INDEX ON blob_entries (key);""")
            conn.commit()
        except:
            logging.debug("Cannot setup")
            pass
        finally:
            if conn is not None:
                conn.close()

    def count_entries(self):
        with sqlite3.connect(self.location) as conn:
            try:
                c = conn.cursor()
                c.execute("SELECT COUNT(value) FROM cache_entries")
                return c.fetchone()[0]
            except Exception as e:
                logging.debug("Cannot count entries. error = {err}".format(err=e))
                return None

    def retrieve_keys(self):
        with sqlite3.connect(self.location) as conn:
            try:
                c = conn.cursor()
                c.execute("SELECT key FROM cache_entries")
                rows = c.fetchall()
                if rows:
                    return [x[0] for x in rows]
            except Exception as e:
                logging.debug("Cannot count entries. error = {err}".format(err=e))
                return None

    def __retrieve(self, key):
        ''' Retrieve file location from cache DB
        '''
        with sqlite3.connect(self.location) as conn:
            try:
                c = conn.cursor()
                c.execute("SELECT value FROM cache_entries WHERE key = ?", (key,))
                result = c.fetchone()
                if result is None or len(result) != 1:
                    logging.debug("There's no entry with key={key}".format(key=key))
                    return None
                else:
                    return result[0]
            except Exception as e:
                logging.debug("Cannot retrieve: {e}".format(e=e))
                return None

    def has_key(self, key):
        return self.__retrieve(key) is not None

    def __insert(self, key, value):
        '''
        Insert a new key to database
        '''
        if self.__retrieve(key) is not None:
            logging.debug("Cache entry exists, cannot insert a new entry with key='{key}'".format(key=key))
            return False
        with sqlite3.connect(self.location) as conn:
            try:
                c = conn.cursor()
                c.execute("INSERT INTO cache_entries (key, value) VALUES (?,?)", (key, value))
                conn.commit()
                return True
            except Exception as e:
                # NOTE: A cache error can be forgiven, no?
                logging.debug("Cache Error: Cannot insert | Detail = %s" % (e,))
                return False
                pass

    def __delete(self, key):
        ''' Delete file key from database
        '''
        with sqlite3.connect(self.location) as conn:
            try:
                c = conn.cursor()
                c.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                conn.commit()
            except Exception as e:
                logging.debug("Cannot delete: {e}".format(e=e))
                return None
                pass

    INTERNAL_BLOB = "JICACHE_INTERNAL_BLOB"

    def __insert_internal_blob(self, key, blob, compressed=True):
        ''' This method will insert blob data to blob table
        '''
        with sqlite3.connect(self.location) as conn:
            conn.isolation_level = None
            c = conn.cursor()
            try:
                compressed_flag = 1 if compressed else 0
                if compressed:
                    blob = zlib.compress(blob)
                c.execute("BEGIN")
                c.execute("INSERT INTO cache_entries (key, value) VALUES (?,?)", (key, JiCache.INTERNAL_BLOB))
                c.execute("INSERT INTO blob_entries (key, compressed, blob_data) VALUES (?,?,?)", (key, compressed_flag, sqlite3.Binary(blob),))
                c.execute("COMMIT")
                return True
            except Exception as e:
                logging.debug("Cannot insert: {e}".format(e=e))
                return False

    def __delete_internal_blob(self, key):
        ''' This method will insert blob data to blob table
        '''
        with sqlite3.connect(self.location) as conn:
            conn.isolation_level = None
            try:
                c = conn.cursor()
                c.execute("BEGIN")
                c.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                c.execute("DELETE FROM blob_entries WHERE KEY = ?", (key,))
                c.execute("COMMIT")
            except Exception as e:
                logging.debug("Cannot delete: {e}".format(e=e))
                return False
            return True

    def __retrieve_internal_blob(self, key):
        ''' Retrieve file location from cache DB
        '''
        with sqlite3.connect(self.location) as conn:
            try:
                c = conn.cursor()
                c.execute("SELECT compressed, blob_data FROM blob_entries WHERE KEY = ?", (key,))
                result = c.fetchone()
                if not result:
                    logging.debug("There's no blob entry with key={key}".format(key=key))
                    logging.debug("result = {res}".format(res=result))
                    return None
                else:
                    compressed, blob_data = result
                    logging.debug("retrieving internal BLOB (key={key} | len={ln} | compressed={c})".format(key=key, ln=len(blob_data), c=compressed))
                    return blob_data if not compressed else zlib.decompress(blob_data)
            except Exception as e:
                logging.debug("Cannot retrieve: {e}".format(e=e))
                return None
            return True

    def insert_blob(self, key, blob):
        if self.__retrieve(key) is not None:
            logging.info("Key exists, cannot insert entry with key='{key}'".format(key=key))
            return False
        elif self.use_internal_blob:
            # insert to database
            logging.debug("Insert BLOB internally")
            # TODO: should the compressed field be in the cache_entries table instead?
            return self.__insert_internal_blob(key, blob, compressed=True)
        else:
            logging.debug("Inserting a new blob with key = {key}".format(key=key))
            # Allocate a new cache file
            blob_key = str(uuid.uuid1())
            blob_file = os.path.join(self.blob_location, blob_key)
            while os.path.exists(blob_file):
                blob_key = str(uuid.uuid1())
                blob_file = os.path.join(self.blob_location, blob_key)
                # try to write BLOB content to file
            FileHelper.save(blob_file, blob)
            if not self.__insert(key, blob_key):
                # Cannot insert key, delete the file
                os.unlink(blob_file)
                return False
            else:
                return True

    def retrieve_blob(self, key, encoding=None):
        blob_key = self.__retrieve(key)
        if blob_key is None:
            return None
        if not blob_key:
            raise Exception("Invalid blob_key")
        elif blob_key == JiCache.INTERNAL_BLOB:
            blob_data = self.__retrieve_internal_blob(key)
            return blob_data if not encoding else blob_data.decode(encoding)
        else:
            logging.debug("Key[{key}] -> [{blob_key}]".format(key=key, blob_key=blob_key))
            blob_file = os.path.join(self.blob_location, blob_key)
            return FileHelper.read(blob_file)

    def delete_blob(self, key):
        blob_key = self.__retrieve(key)
        if blob_key == JiCache.INTERNAL_BLOB:
            # blah
            logging.debug("deleting internal BLOB")
            self.__delete_internal_blob(key)
        else:
            logging.debug("deleting BLOB from file")
            blob_file = os.path.join(self.blob_location, blob_key)
            os.unlink(blob_file)
            self.__delete(key)

# quick helper functions
    def insert_string(self, key, a_string, encoding='utf-8'):
        return self.insert_blob(key, a_string.encode(encoding))

    def retrieve_string(self, key, encoding='utf-8'):
        return self.retrieve_blob(key, encoding=encoding)

    def insert_file(self, key, file_path):
        with open(file_path, 'rb') as input_file:
            byte_data = input_file.read()
            return self.insert_blob(key, byte_data)
