# -*- coding: utf-8 -*-

"""
Chirptext Arsenal - Cache utilities
"""

# This code is a part of chirptext library: https://github.com/letuananh/chirptext
# :copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
# :license: MIT, see LICENSE for more details.

import os
import uuid
import logging
import sqlite3
import zlib

from .leutile import FileHelper


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

def getLogger():
    return logging.getLogger(__name__)


class JiCache:
    """ Cache textual/binary content using an SQLite file (with internal blob or an external folder)
    """
    def __init__(self, location, blob_location=None, use_internal_blob=True):
        self.location = os.path.abspath(os.path.expanduser(location))
        self.blob_location = os.path.abspath(os.path.expanduser(blob_location)) if blob_location else self.location + '.blob'
        self.use_internal_blob = use_internal_blob
        logger = getLogger()
        logger.info("Cache DB location    : {location}".format(location=self.location))
        if not use_internal_blob:
            logger.info("Blob location        : {blob_loc}".format(blob_loc=self.blob_location))
        else:
            logger.info("Store BLOB internally: {storage_mode}".format(storage_mode=self.use_internal_blob))
        # self.setup()

    def setup(self):
        if not os.path.isfile(self.location) or os.path.getsize(self.location) == 0:
            getLogger().debug("Setting up DB")
            # create dir to store blobs
            if not self.use_internal_blob:
                FileHelper.create_dir(self.blob_location)
            with sqlite3.connect(self.location) as conn:
                c = conn.cursor()
                # Create tables
                c.execute("""CREATE TABLE IF NOT EXISTS cache_entries (key UNIQUE, value);""")
                c.execute("""CREATE INDEX IF NOT EXISTS CACHE_ENTRIES_KEY_INDEX ON cache_entries (key);""")
                c.execute("""CREATE TABLE IF NOT EXISTS blob_entries (key UNIQUE, compressed, blob_data);""")
                c.execute("""CREATE INDEX IF NOT EXISTS BLOB_ENTRIES_KEY_INDEX ON blob_entries (key);""")
                conn.commit()

    def get_conn(self):
        self.setup()
        return sqlite3.connect(self.location)

    def count_entries(self):
        with self.get_conn() as conn:
            try:
                c = conn.cursor()
                c.execute("SELECT COUNT(value) FROM cache_entries")
                return c.fetchone()[0]
            except Exception:
                getLogger().exception("Cannot count entries")
                return None

    def retrieve_keys(self):
        with self.get_conn() as conn:
            try:
                c = conn.cursor()
                c.execute("SELECT key FROM cache_entries")
                rows = c.fetchall()
                if rows:
                    return [x[0] for x in rows]
            except Exception:
                getLogger().exception("Cannot retrieve keys")
                return None

    def __retrieve(self, key):
        """ Retrieve file location from cache DB
        """
        with self.get_conn() as conn:
            try:
                c = conn.cursor()
                if key is None:
                    c.execute("SELECT value FROM cache_entries WHERE key IS NULL")
                else:
                    c.execute("SELECT value FROM cache_entries WHERE key = ?", (key,))
                result = c.fetchone()
                if result is None or len(result) != 1:
                    getLogger().info("There's no entry with key={key}".format(key=key))
                    return None
                else:
                    return result[0]
            except Exception:
                getLogger().exception("Cannot retrieve")
                return None

    def has_key(self, key):
        return key in self

    def __contains__(self, key):
        return self.__retrieve(key) is not None

    def __insert(self, key, value):
        """
        Insert a new key to database
        """
        if key in self:
            getLogger().warning("Cache entry exists, cannot insert a new entry with key='{key}'".format(key=key))
            return False
        with self.get_conn() as conn:
            try:
                c = conn.cursor()
                c.execute("INSERT INTO cache_entries (key, value) VALUES (?,?)", (key, value))
                conn.commit()
                return True
            except Exception as e:
                # NOTE: A cache error can be forgiven, no?
                getLogger().debug("Cache Error: Cannot insert | Detail = %s" % (e,))
                return False

    def __delete(self, key):
        """ Delete file key from database
        """
        with self.get_conn() as conn:
            try:
                c = conn.cursor()
                c.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                conn.commit()
            except Exception:
                getLogger().exception("Cannot delete")
                return None

    INTERNAL_BLOB = "JICACHE_INTERNAL_BLOB"

    def __insert_internal_blob(self, key, blob, compressed=True):
        """ This method will insert blob data to blob table
        """
        with self.get_conn() as conn:
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
            except Exception:
                getLogger().debug("Cannot insert")
                return False

    def __delete_internal_blob(self, key):
        """ This method will insert blob data to blob table
        """
        with self.get_conn() as conn:
            conn.isolation_level = None
            try:
                c = conn.cursor()
                c.execute("BEGIN")
                if key is None:
                    c.execute("DELETE FROM cache_entries WHERE key IS NULL")
                    c.execute("DELETE FROM blob_entries WHERE KEY IS NULL")
                else:
                    c.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                    c.execute("DELETE FROM blob_entries WHERE KEY = ?", (key,))
                c.execute("COMMIT")
            except Exception:
                getLogger().debug("Cannot delete")
                return False
            return True

    def __retrieve_internal_blob(self, key):
        """ Retrieve file location from cache DB
        """
        logger = getLogger()
        with self.get_conn() as conn:
            try:
                c = conn.cursor()
                if key is None:
                    c.execute("SELECT compressed, blob_data FROM blob_entries WHERE KEY IS NULL")
                else:
                    c.execute("SELECT compressed, blob_data FROM blob_entries WHERE KEY = ?", (key,))
                result = c.fetchone()
                if not result:
                    logger.debug("There's no blob entry with key={key}".format(key=key))
                    logger.debug("result = {res}".format(res=result))
                    return None
                else:
                    compressed, blob_data = result
                    logger.debug("retrieving internal BLOB (key={key} | len={ln} | compressed={c})".format(key=key, ln=len(blob_data), c=compressed))
                    return blob_data if not compressed else zlib.decompress(blob_data)
            except Exception:
                getLogger().exception("Cannot retrieve internal blob (key={})".format(key))
                return None

    def insert_blob(self, key, blob):
        if self.__retrieve(key) is not None:
            getLogger().warning("Key exists, cannot insert entry with key='{key}'".format(key=key))
            return False
        elif self.use_internal_blob:
            # insert to database
            getLogger().debug("Insert BLOB internally")
            # TODO: should the compressed field be in the cache_entries table instead?
            return self.__insert_internal_blob(key, blob, compressed=True)
        else:
            getLogger().debug("Inserting a new blob with key = {key}".format(key=key))
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
        """ Retrieve blob in binary format (or string format if encoding is provided) """
        blob_key = self.__retrieve(key)
        if blob_key is None:
            return None
        if not blob_key:
            raise Exception("Invalid blob_key")
        elif blob_key == JiCache.INTERNAL_BLOB:
            blob_data = self.__retrieve_internal_blob(key)
            return blob_data if not encoding else blob_data.decode(encoding)
        else:
            getLogger().debug("Key[{key}] -> [{blob_key}]".format(key=key, blob_key=blob_key))
            blob_file = os.path.join(self.blob_location, blob_key)
            return FileHelper.read(blob_file)

    def delete_blob(self, key):
        blob_key = self.__retrieve(key)
        logger = getLogger()
        if blob_key is None:
            logger.debug("Nothing to delete for key = {}".format(key))
        elif blob_key == JiCache.INTERNAL_BLOB:
            # blah
            logger.debug("deleting internal BLOB")
            self.__delete_internal_blob(key)
        else:
            logger.debug("deleting BLOB from file")
            logger.debug("Blob loc: {}".format(self.blob_location))
            logger.debug("Blob key: {}".format(blob_key))
            blob_file = os.path.join(self.blob_location, blob_key)
            os.unlink(blob_file)
            self.__delete(key)

    def insert_string(self, key, a_string, encoding='utf-8'):
        return self.insert_blob(key, a_string.encode(encoding))

    def retrieve_string(self, key, encoding='utf-8'):
        return self.retrieve_blob(key, encoding=encoding)

    def insert_file(self, key, file_path):
        with open(file_path, 'rb') as input_file:
            byte_data = input_file.read()
            return self.insert_blob(key, byte_data)
