from chirptext import Counter, TextReport
from chirptext.leutile import LOREM_IPSUM

# ------------------------------------------------------------------------------
# Basic utilities
# ------------------------------------------------------------------------------
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


# ------------------------------------------------------------------------------
# Sample text report
# ------------------------------------------------------------------------------
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


# ------------------------------------------------------------------------------
# Web fetcher
# ------------------------------------------------------------------------------
from chirptext import WebHelper

web = WebHelper('~/tmp/webcache.db')
data = web.fetch('https://letuananh.github.io/test/data.json')
print(data)
data_json = web.fetch_json('https://letuananh.github.io/test/data.json')
print(data_json)
