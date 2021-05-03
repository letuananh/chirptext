.. _recipes:

Common Recipes
==============

Web fetcher
-----------

.. code:: python

   from chirptext import WebHelper

   web = WebHelper('~/tmp/webcache.db')
   data = web.fetch('https://letuananh.github.io/test/data.json')
   data
   >>> b'{ "name": "Kungfu Panda" }\n'
   data_json = web.fetch_json('https://letuananh.github.io/test/data.json')
   data_json
   >>> {'name': 'Kungfu Panda'}

Using Counter
-------------

.. code:: python

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

Output
~~~~~~

::

   Letters: 377 
   Consonants: 212 
   Vowels: 165 
   i: 42 
   e: 37 
   t: 32 
   o: 29 
   a: 29 

Sample TextReport
-----------------

.. code:: python

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

.. _output-1:

Output
~~~~~~

::

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
