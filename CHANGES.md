# Chirptext changelog

## 15 Mar 2022

- Fix `ttl.read_json()` bug
- Fix `token.surface` related bug (`token.surface()` is a method, not a property)

## 20 May 2021

- v >= 0.1.2: Fix `newline` and `encoding` keywords missing in `chio.write_csv()` and `chio.write_tsv()`

## 1 Jun 2020

- Improved texttaglib (lite) module
  - Better TTL-JSON support
  - Standardized TTL access methods (find(), find_all() to get_tag(), get_tags())
- Improved chirptext.sino module (Kangxi radical information)
- Rename TextReport.file to TextReport.stream (more intuitive)
- Show fewer mecab related warnings
- Use Markdown for PyPI project README file

## 9 Sep 2015

- Reorganise project structure
