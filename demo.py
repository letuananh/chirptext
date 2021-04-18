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
rp.write("This line goes to standard output")

rp1 = TextReport(TextReport.STDOUT)  # same as above
rp1.write("This line goes to standard output")

rp2 = TextReport('~/tmp/my-report.txt')  # output to a file
rp2.write("This is a line in my-report.txt")

rp3 = TextReport.null()  # ouptut to /dev/null, i.e. nowhere
rp3.write("This line goes no where")

rp4 = TextReport.string()  # output to a string. Call rp.content() to get the string
rp4.write("This line will be stored in a string buffer")

rp5 = TextReport(TextReport.STRINGIO)  # same as above
rp5.write("This line will also be stored in a string buffer")

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
