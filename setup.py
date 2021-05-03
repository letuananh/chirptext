#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Setup script for ChirpText.

Latest version can be found at https://github.com/letuananh/chirptext

:copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
:license: MIT, see LICENSE for more details.
'''

import io
from setuptools import setup


def read(*filenames, **kwargs):
    ''' Read contents of multiple files and join them together '''
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


# readme_file = 'README.rst' if os.path.isfile('README.rst') else 'README.md'
readme_file = 'README.md'
long_description = read(readme_file)
pkg_info = {}
exec(read('chirptext/__version__.py'), pkg_info)


setup(
    name='chirptext',  # package file name (<package-name>-version.tar.gz)
    version=pkg_info['__version__'],
    url=pkg_info['__url__'],
    project_urls={
        "Bug Tracker": "https://github.com/letuananh/chirptext/issues",
        "Source Code": "https://github.com/letuananh/chirptext/"
    },
    keywords=["nlp", "mecab", "language", "linguistics", "vietnamese", "japanese", "chinese", "kanji", "radical"],
    license=pkg_info['__license__'],
    author=pkg_info['__author__'],
    tests_require=[],
    install_requires=[],
    python_requires=">=3.5",
    author_email=pkg_info['__email__'],
    description=pkg_info['__description__'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['chirptext'],
    package_data={'chirptext': ['data/luke/swadesh/*.txt',
                                'data/sino/*.csv']},
    include_package_data=True,
    platforms='any',
    test_suite='test',
    # Reference: https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=['Programming Language :: Python',
                 'Development Status :: {}'.format(pkg_info['__status__']),
                 'Natural Language :: English',
                 'Natural Language :: Vietnamese',
                 'Natural Language :: Japanese',
                 'Natural Language :: Chinese (Traditional)',
                 'Environment :: Plugins',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: {}'.format(pkg_info['__license__']),
                 'Operating System :: OS Independent',
                 'Topic :: Text Processing',
                 'Topic :: Software Development :: Libraries :: Python Modules']
)
