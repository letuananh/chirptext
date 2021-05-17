ChirpText is a collection of text processing tools for Python 3.

[![Documentation Status](https://readthedocs.org/projects/chirptext/badge/?version=latest)](https://chirptext.readthedocs.io/en/latest/?badge=latest)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/letuananh/chirptext.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/letuananh/chirptext/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/letuananh/chirptext.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/letuananh/chirptext/context:python)

It is not meant to be a powerful tank like the popular NTLK but a small package which you can pip-install anywhere and write a few lines of code to process textual data.

# Main features

* Simple file data manipulation using an enhanced `open()` function (txt, gz, binary, etc.)
* CSV helper functions
* Parse Japanese text with mecab library (Does not require `mecab-python3` package even on Windows, only a binary release (i.e. `mecab.exe`) is required)
* Built-in "lite" [text annotation formats](https://pypi.org/project/texttaglib/) (`texttaglib` TTL/CSV and TTL/JSON)
* Helper functions and useful data for processing English, Japanese, Chinese and Vietnamese.
* Application configuration files management which can make educated guess about config files' whereabouts
* Quick text-based report generation

# Installation

`chirptext` is available on [PyPI](https://pypi.org/project/chirptext/) and can be installed using pip

```bash
pip install chirptext
```

# Parsing Japanese text

`chirptext` supports parsing Japanese text using different parsers (mecab, Janome, and igo-python)

```python
>>> from chirptext import deko
>>> sent = deko.parse('猫が好きです。')
>>> sent.tokens
['`猫`<0:1>', '`が`<1:2>', '`好き`<2:4>', '`です`<4:6>', '`。`<6:7>']
>>> sent.tokens.values()
['猫', 'が', '好き', 'です', '。']
>>> sent[0]
`猫`<0:1>
>>> sent[0].pos
'名詞'
>>> sent[1].lemma
'が'
>>> sent[2].reading
'スキ'

# tokenize
>>> deko.tokenize('猫が好きです。')
['猫', 'が', '好き', 'です', '。']

# split sentences
>>> deko.tokenize_sent("猫が好きです。\n犬も好きです。")
['猫が好きです。', '犬も好きです。']

# parse a document (i.e. multiple sentences)
>>> doc = deko.parse_doc("猫が好きです。\n犬も好きです。")
>>> for sent in doc:
...     print(sent, sent.tokens.values())
... 
猫が好きです。 ['猫', 'が', '好き', 'です', '。']
犬も好きです。 ['犬', 'も', '好き', 'です', '。']
```

Notes: At least one of the following tools must be installed to use chirptext Japanese parsing:

1. mecab: [http://taku910.github.io/mecab/#download](http://taku910.github.io/mecab/#download)
2. Janome: available on PyPI, install with `pip install Janome`
3. igo-python: available on PyPI, install with `pip install igo-python`

# Convenient IO APIs

```python
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
```

# Sample TextReport

```python
# a string report
rp = TextReport()  # by default, TextReport will write to standard output, i.e. terminal
rp = TextReport(TextReport.STDOUT)  # same as above
rp = TextReport('~/tmp/my-report.txt')  # output to a file
rp = TextReport.null()  # ouptut to /dev/null, i.e. nowhere
rp = TextReport.string()  # output to a string. Call rp.content() to get the string
rp = TextReport(TextReport.STRINGIO)  # same as above

# TextReport will close the output stream automatically by using the with statement
with TextReport.string() as rp:
    rp.header("Lorem Ipsum Analysis", level="h0")
    rp.header("Raw", level="h1")
    rp.print(LOREM_IPSUM)
    rp.header("Top 5 most common letters")
    ct.summarise(report=rp, limit=5)
    print(rp.content())
```

## Output
```
+---------------------------------------------------------------------------------- 
| Lorem Ipsum Analysis 
+---------------------------------------------------------------------------------- 
 
Raw 
------------------------------------------------------------ 
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. 
 
Top 5 most common letters
------------------------------------------------------------ 
i: 42 
e: 37 
t: 32 
o: 29 
a: 29 
```

# Useful links

- Documentation: https://chirptext.readthedocs.io
- Source code: https://github.com/letuananh/chirptext/
- PyPI: https://pypi.org/project/chirptext/
