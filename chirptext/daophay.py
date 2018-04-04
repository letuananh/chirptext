# -*- coding: utf-8 -*-

'''
Dao Phay library: A collection of tools for processing Vietnamese text using Python.

Latest version can be found at https://github.com/letuananh/chirptext

:copyright: (c) 2012 Le Tuan Anh <tuananh.ke@gmail.com>
:license: MIT, see LICENSE for more details.
'''

# in lower case: aàảãáạăằẳẵắặâầẩẫấậbcdđeèẻẽéẹêềểễếệghiìỉĩíịklmnoòỏõóọôồổỗốộơờởỡớợpqrstuùủũúụưừửữứựvxyỳỷỹýỵ
VIETNAMESE_ALPHABET_ORDER = 'aAàÀảẢãÃáÁạẠăĂằẰẳẲẵẴắẮặẶâÂầẦẩẨẫẪấẤậẬbBcCdDđĐeEèÈẻẺẽẼéÉẹẸêÊềỀểỂễỄếẾệỆgGhHiIìÌỉỈĩĨíÍịỊkKlLmMnNoOòÒỏỎõÕóÓọỌôÔồỒổỔỗỖốỐộỘơƠờỜởỞỡỠớỚợỢpPqQrRsStTuUùÙủỦũŨúÚụỤưƯừỪửỬữỮứỨựỰvVxXyYỳỲỷỶỹỸýÝỵỴ'
VIETNAMESE_SORTING_DICT = dict((x, VIETNAMESE_ALPHABET_ORDER.index(x)) for x in VIETNAMESE_ALPHABET_ORDER)
python_sorted = sorted


# ------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------

def vnorder_char(c):
    return VIETNAMESE_SORTING_DICT[c] if c in VIETNAMESE_SORTING_DICT else ord(c)


def vnorder(s):
    return [vnorder_char(c) for c in s]


def sorted(list_of_strings):
    return python_sorted(list_of_strings, key=vnorder)
