# -*- coding: utf-8 -*-

'''
Chirp Text - Minimalist Text Processing Library

Latest version can be found at https://github.com/letuananh/chirptext

:copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
:license: MIT, see LICENSE for more details.
'''

########################################################################

from .__version__ import __author__, __email__, __copyright__, __maintainer__
from .__version__ import __credits__, __license__, __description__, __url__
from .__version__ import __version_major__, __version_long__, __version__, __status__

from .leutile import uniquify, header, confirm, piter
from .leutile import Timer, Counter, FileHub, TextReport, FileHelper, AppConfig
from .arsenal import JiCache
from .anhxa import DataObject
from .chirpnet import SmartURL, WebHelper
from . import texttaglib as ttl

__all__ = ["uniquify", "header", "confirm", "piter",
           "Timer", "Counter",
           "TextReport", "FileHub", "FileHelper", "AppConfig",
           "JiCache", "SmartURL", "WebHelper",
           "DataObject", "ttl",
           "__version__", "__author__", "__description__", "__copyright__"]
