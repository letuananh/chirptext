ChirpText is a collection of text processing tools for Python.
It is not meant to be a powerful tank like the popular NTLK but a small package which you can pip-install anywhere and write a few lines of code to process textual data.

# Main features

* **[New]** Does not require `mecab-python3` package to use MeCab/Deko on Windows. Only binary release (`mecab.exe`) is required.
* Text annotation framework (TTL, a.k.a TextTagLib format) which can import/export JSON or human-readable text files
* Helper functions and useful data for processing English, Japanese, Chinese and Vietnamese.
* Quick text-based report generation
* Application configuration files management which can make educated guess about config files' whereabouts
* Web fetcher with responsible web crawling ethics (support caching out of the box)
* CSV helper functions
* Console application template

Project homepage: [https://github.com/letuananh/chirptext](https://github.com/letuananh/chirptext)

# Installation

```bash
pip install chirptext
# pip script sometimes doesn't work properly, so you may want to try this instead
python3 -m pip install chirptext
```
**Note**: chirptext library does not support Python 2 anymore. Please update to Python 3 to use this package.

# Sample codes

## Using MeCab on Windows
You can download mecab binary package from [http://taku910.github.io/mecab/#download](http://taku910.github.io/mecab/#download) and install it.
After installed you can try:
```python
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
```

If you installed MeCab to a custom location, for example `C:\mecab\bin\mecab.exe`, try
```python
>>> deko.set_mecab_bin("C:\\mecab\\bin\\mecab.exe")
>>> deko.get_mecab_bin()
'C:\\mecab\\bin\\mecab.exe'

# Just that & now you can use mecab
>>> deko.parse('雨が降る。').words
['雨', 'が', '降る', '。']
```

## Web fetcher

```python
from chirptext import WebHelper

web = WebHelper('~/tmp/webcache.db')
data = web.fetch('https://letuananh.github.io/test/data.json')
data
>>> b'{ "name": "Kungfu Panda" }\n'
data_json = web.fetch_json('https://letuananh.github.io/test/data.json')
data_json
>>> {'name': 'Kungfu Panda'}
```

## Using Counter

```python
from chirptext import Counter, TextReport
from chirptext.leutile import LOREM_IPSUM

ct = Counter()
vc = Counter()  # vowel counter
for char in LOREM_IPSUM:
    if char == ' ':
        continue
    ct.count(char)
    vc.count("Letters")
    if char in 'auieo':
        vc.count("Vowels")
    else:
        vc.count("Consonants")
vc.summarise()
ct.summarise(byfreq=True, limit=5)
```

### Output

```
Letters: 377 
Consonants: 212 
Vowels: 165 
i: 42 
e: 37 
t: 32 
o: 29 
a: 29 
```

## Sample TextReport

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

### Output
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
