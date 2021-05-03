.. chirptext documentation master file, created by
   sphinx-quickstart on Mon May  3 11:34:14 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to chirptext's documentation!
=====================================

ChirpText, an `open source and free software <https://github.com/letuananh/chirptext/>`_,
is a collection of  text processing tools for Python.

.. image:: https://img.shields.io/lgtm/alerts/g/letuananh/chirptext.svg?logo=lgtm&logoWidth=18
   :target: https://lgtm.com/projects/g/letuananh/chirptext/alerts/
.. image:: https://img.shields.io/lgtm/grade/python/g/letuananh/chirptext.svg?logo=lgtm&logoWidth=18
   :target: https://lgtm.com/projects/g/letuananh/chirptext/context:python

It is not meant to be a powerful tank like the popular NTLK but a small
package which you can pip-install anywhere and write a few lines of code
to process textual data.

Main features
=============

-  Parse Japanese text (Does not require ``mecab-python3`` package even on Windows, only a binary release
   (i.e. ``mecab.exe``) is required)
-  Built-in “lite” `text annotation formats <https://pypi.org/project/speach/>`__ (TTL/CSV and TTL/JSON)
-  Helper functions and useful data for processing English, Japanese, Chinese and Vietnamese.
-  Enhanced ``open()`` function that support common text-based and binary-based format (txt, gz, csv, tsv, json, etc.)
-  Quick text-based report generation
-  Application configuration management which can make educated guess about config files’ whereabouts
-  **((Experimental)** Web fetcher with responsible web crawling ethics
   (support caching out of the box)
-  **(Experimental)** Console application template

Installation
============

Chirptext is available on `PyPI <https://pypi.org/project/chirptext/>`_ and can be installed using ``pip install``

.. code:: bash

   python install chirptext

**Note**: chirptext library does not support Python 2 anymore. Please
update to Python 3 to use this package.

Sample codes
============

Using MeCab on Windows
----------------------

You can download mecab binary package from
http://taku910.github.io/mecab/#download and install it.
After installed you can try:

.. code:: python

   >>> from chirptext import deko
   >>> sent = deko.parse('猫が好きです。')
   >>> sent.tokens
   [[猫(名詞-一般/*/*|猫|ネコ|ネコ)], [が(助詞-格助詞/一般/*|が|ガ|ガ)], [好き(名詞-形容動詞語幹/*/*|好き|スキ|スキ)], [です(助動詞-*/*/*|です|デス|デス)], [。(記号-句点/*/*|。|。|。)], [EOS(-//|||)]]
   >>> sent.words
   ['猫', 'が', '好き', 'です', '。']
   >>> sent[0].pos
   '名詞'
   >>> sent[0].root
   '猫'
   >>> sent[0].reading
   'ネコ'

If you installed MeCab to a custom location, for example
``C:\mecab\bin\mecab.exe``, try

.. code:: python

   >>> deko.set_mecab_bin("C:\\mecab\\bin\\mecab.exe")
   >>> deko.get_mecab_bin()
   'C:\\mecab\\bin\\mecab.exe'

   # Just that & now you can use mecab
   >>> deko.parse('雨が降る。').words
   ['雨', 'が', '降る', '。']

Convenient IO APIs
------------------

.. code:: python

   >>> from chirptext import chio
   >>> chio.write_tsv('data/test.tsv', [['a', 'b'], ['c', 'd']])
   >>> chio.read_tsv('data/tes.tsv')
   [['a', 'b'], ['c', 'd']]

   >>> chio.write_file('data/content.tar.gz', 'Support writing to .tar.gz file')
   >>> chio.read_file('data/content.tar.gz')
   'Support writing to .tar.gz file'

   >>> for row in chio.read_tsv_iter('data/test.tsv'):
   ...     print(row)
   ... 
   ['a', 'b']
   ['c', 'd']

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   recipes
   api

Useful links
------------

- Chirptext source code: https://github.com/letuananh/chirptext/
- Chirptext documentation: https://chirptext.readthedocs.io/
- Chirptext on PyPI: https://pypi.org/project/chirptext/

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
