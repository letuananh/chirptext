# -*- coding: utf-8 -*-

'''
Chirp Net - Web utilities

Latest version can be found at https://github.com/letuananh/chirptext

:copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
:license: MIT, see LICENSE for more details.
'''

import os
from io import BytesIO
import gzip
import logging
import json
from urllib.request import Request, urlopen
from urllib.error import URLError
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode, quote

from chirptext.arsenal import JiCache


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

def getLogger():
    return logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------

class SmartURL(object):
    ''' Smart URL supports URL manipulation '''

    def __init__(self, raw_url, quoted=False):
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
            self.process(quoted)

    def get_filename(self):
        return os.path.basename(self.p.path)

    def get_filename_noext(self):
        return os.path.splitext(self.get_filename())[0]

    def get_file_ext(self):
        return os.path.splitext(self.get_filename())[1]

    def process(self, quoted=False):
        ''' Parse an URL '''
        self.p = urlparse(self.raw)
        self.scheme = self.p.scheme
        self.netloc = self.p.netloc
        self.opath = self.p.path if not quoted else quote(self.p.path)
        self.path = [x for x in self.opath.split('/') if x]
        self.params = self.p.params
        self.query = parse_qs(self.p.query, keep_blank_values=True)
        self.fragment = self.p.fragment

    def __str__(self):
        flatd = [(k, v[0] if len(v) == 1 else v) for k, v in self.query.items()]
        return urlunparse((self.scheme, self.netloc, '/'.join(self.path), self.params, urlencode(flatd), self.fragment))


class WebHelper(object):
    ''' a wget like utility for Python '''

    def __init__(self, cache=None):
        if cache is None or isinstance(cache, JiCache):
            self.cache = cache
        else:
            self.cache = JiCache(location=str(cache))

    @staticmethod
    def encode_url(url):
        return str(SmartURL(url, quoted=True))

    def fetch(self, url, encoding=None, force_refetch=False, nocache=False, quiet=True):
        ''' Fetch a HTML file as binary'''
        try:
            if not force_refetch and self.cache is not None and url in self.cache:
                # try to look for content in cache
                logging.debug('Retrieving content from cache for {}'.format(url))
                return self.cache.retrieve_blob(url, encoding)
            encoded_url = WebHelper.encode_url(url)
            req = Request(encoded_url, headers={'User-Agent': 'Mozilla/5.0'})
            # support gzip
            req.add_header('Accept-encoding', 'gzip, deflate')
            # Open URL
            getLogger().info("Fetching: {url} |".format(url=url))
            response = urlopen(req)
            content = response.read()
            # unzip if required
            if 'Content-Encoding' in response.info() and response.info().get('Content-Encoding') == 'gzip':
                # unzip
                with gzip.open(BytesIO(content)) as gzfile:
                    content = gzfile.read()
            # update cache if required
            if self.cache is not None and not nocache:
                if url not in self.cache:
                    self.cache.insert_blob(url, content)
            return content.decode(encoding) if content and encoding else content
        except URLError as e:
            error_message = "Unknown fetching error"
            if hasattr(e, 'reason'):
                error_message = 'We failed to reach {}. Reason: {}'.format(url, e.reason)
            elif hasattr(e, 'code'):
                error_message = 'The server couldn\'t fulfill the request. Error code: {}'.format(e.code)
            # done!
            if not quiet:
                raise
            else:
                getLogger().debug(error_message)
        return None

    def fetch_json(self, *args, **kwargs):
        output = self.fetch(*args, **kwargs)
        if output is not None:
            return json.loads(output)
        else:
            return None

    def download(self, url, path, force_refetch=False, nocache=False):
        ''' Download a file at $url and save it to $path
        '''
        # Enable cache
        if os.path.isfile(path):
            getLogger().info("File exists, download task skipped -> {path}".format(path=path))
            return True
        try:
            # Open URL
            getLogger().info("Downloading: {url} -> {path}".format(url=url, path=path))
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
                getLogger().exception('We failed to reach a server. Reason: %s' % (e.reason,))
            elif hasattr(e, 'code'):
                getLogger().exception("The server couldn't fulfill the request. Error code: {code}".format(code=e.code))
            else:
                # everything is fine
                getLogger().exception("Unknown error: %s" % (e,))
        return False
