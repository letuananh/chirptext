#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Chirp Net - Web utilities

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
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Le Tuan Anh"
__email__ = "<tuananh.ke@gmail.com>"
__status__ = "Prototype"

#-----------------------------------------------------------------------------

import os
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode


class SmartURL(object):
    ''' Smart URL supports URL manipulation '''

    def __init__(self, raw_url):
        self.raw = raw_url
        self.p = None
        self.scheme = None
        self.netloc = None
        self.opath = None
        self.path = None
        self.params = None
        self.query = None
        self.fragment = None
        if self.raw:
            self.process()

    def get_filename(self):
        return os.path.basename(self.p.path)

    def get_filename_noext(self):
        return os.path.splitext(self.get_filename())[0]

    def get_file_ext(self):
        return os.path.splitext(self.get_filename())[1]

    def process(self):
        ''' Parse an URL '''
        self.p = urlparse(self.raw)
        self.scheme = self.p.scheme
        self.netloc = self.p.netloc
        self.opath = self.p.path
        self.path = [x for x in self.p.path.split('/') if x]
        self.params = self.p.params
        self.query = parse_qs(self.p.query, keep_blank_values=True)
        self.fragment = self.p.fragment

    def __str__(self):
        flatd = [(k, v[0] if len(v) == 1 else v) for k, v in self.query.items()]
        return urlunparse((self.scheme, self.netloc, '/'.join(self.path), self.params, urlencode(flatd), self.fragment))


class WebHelper(object):
    ''' a wget like utility for Python '''

    def __init__(self, cache=None):
        self.cache = cache

    @staticmethod
    def encode_url(url):
        return url.replace(" ", "%20").replace('%3A', ':').replace('%2F', '/')

    def fetch(self, url, encoding=None, force_refetch=False, nocache=False):
        ''' Fetch a HTML file as binary'''
        try:
            if not force_refetch and self.cache is not None and url in self.cache:
                # try to look for content in cache
                logging.debug('Retrieving content from cache for {}'.format(url))
                return self.cache.retrieve_blob(url, encoding)
            logging.info("Fetching: {url} |".format(url=url))
            url = WebHelper.encode_url(url)
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            # Open URL
            response = urlopen(req)
            content = response.read()
            # update cache if required
            if self.cache is not None and not nocache:
                if url not in self.cache:
                    self.cache.insert_blob(url, content)
            return content
        except URLError as e:
            if hasattr(e, 'reason'):
                logging.exception(e, 'We failed to reach a server. Reason: {}'.format(e.reason))
            elif hasattr(e, 'code'):
                logging.exception('The server couldn\'t fulfill the request. Error code: {}'.format(e.code))
            else:
                # Other exception ...
                logging.exception(e, "Fetching error")
        return None

    def download(self, url, path, force_refetch=False, nocache=False):
        ''' Download a file at $url and save it to $path
        '''
        # Enable cache
        if os.path.isfile(path):
            logging.info("File exists, download task skipped -> {path}".format(path=path))
            return True
        try:
            # Open URL
            logging.info("Downloading: {url} -> {path}".format(url=url, path=path))
            response = self.fetch(url, force_refetch=force_refetch, nocache=nocache)
            if response is not None:
                # Download file
                local_file = open(path, "wb")
                local_file.write(response)
                local_file.close()
                # Finished
                return True
            else:
                return False
        except Exception as e:
            if hasattr(e, 'reason'):
                logging.warning('We failed to reach a server. Reason: %s' % (e.reason,))
            elif hasattr(e, 'code'):
                logging.warning("The server couldn't fulfill the request. Error code: {code}".format(code=e.code))
            else:
                # everything is fine
                logging.warning("Unknown error: %s" % (e,))
        return False
