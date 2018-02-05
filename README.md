ChirpText is a collection of text processing tools for Python.
It is not meant to be a powerful tank like the popular NTLK but a small package which you can pip-install anywhere and write a few lines of code to process textual data.

# Main features

* Quick text-based report generation
* Web fetcher with responsible web crawling ethics (support caching out of the box)
* Text annotation framework (TTL, a.k.a TextTagLib format) which can import/export JSON or human-readable text files
* CSV helper functions
* Helper functions and useful data for processing English, Japanese, Chinese and Vietnamese.
* Console application template
* Application configuration files management which can make educated guess about config files' whereabouts

# Installation

```bash
pip install chirptext
# pip script sometimes doesn't work properly, so you may want to try this instead
python3 -m pip install chirptext
```
**Note**: chirptext library does not support Python 2 anymore. Please update to Python 3 to use this package.

# Sample codes

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
    rp.header("Character Frequency")
    ct.summarise(report=rp)
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
 
Character Frequency 
------------------------------------------------------------ 
i: 42 
e: 37 
t: 32 
o: 29 
a: 29 
u: 28 
n: 24 
r: 22 
l: 21 
s: 18 
d: 18 
m: 17 
c: 16 
p: 11 
q: 5 
,: 4 
.: 4 
g: 3 
b: 3 
v: 3 
x: 3 
f: 3 
L: 1 
U: 1 
D: 1 
h: 1 
E: 1 
```
