import os
import logging
import platform
import subprocess

# Try to use mecab-python3 if it's available
MECAB_PYTHON3 = False
MECAB_LOC = 'mecab'  # location of mecab's binary package
try:
    import MeCab
    MeCab.Tagger().parse("Pythonが好きです。")
    MECAB_PYTHON3 = True
except:
    # use flex-mecab
    try:
        if platform.system() == 'Windows':
            if os.path.isfile("C:\\Program Files (x86)\\MeCab\\bin\\mecab.exe"):
                MECAB_LOC = "C:\\Program Files (x86)\\MeCab\\bin\\mecab.exe"
            elif os.path.isfile("C:\\Program Files\\MeCab\\bin\\mecab.exe"):
                MECAB_LOC = "C:\\Program Files\\MeCab\\bin\\mecab.exe"
            else:
                MECAB_LOC = "mecab.exe"
        elif os.path.isfile('/usr/local/bin/mecab'):
            MECAB_LOC = '/usr/local/bin/mecab'
        else:
            MECAB_LOC = "mecab"
    except:
        pass
    logging.getLogger(__name__).warning("mecab-python3 could not be loaded. mecab binary package will be used ({})".format(MECAB_LOC))


def _register_mecab_loc(location):
    ''' Set MeCab binary location '''
    global MECAB_LOC
    if not os.path.isfile(location):
        logging.getLogger(__name__).warning("Provided mecab binary location does not exist {}".format(location))
    logging.getLogger(__name__).info("Mecab binary is switched to: {}".format(location))
    MECAB_LOC = location


def _get_mecab_loc():
    ''' Get MeCab binary location '''
    return MECAB_LOC


def run_mecab_process(content, *args, **kwargs):
    ''' Use subprocess to run mecab '''
    encoding = 'utf-8' if 'encoding' not in kwargs else kwargs['encoding']
    mecab_loc = kwargs['mecab_loc'] if 'mecab_loc' in kwargs else None
    if mecab_loc is None:
        mecab_loc = MECAB_LOC
    proc_args = [mecab_loc]
    if args:
        proc_args.extend(args)
    output = subprocess.run(proc_args,
                            input=content.encode(encoding),
                            stdout=subprocess.PIPE)
    output_string = os.linesep.join(output.stdout.decode(encoding).splitlines())
    return output_string


def parse(content, *args, **kwargs):
    ''' Use mecab-python3 by default to parse JP text. Fall back to mecab binary app if needed '''
    if 'mecab_loc' not in kwargs and MECAB_PYTHON3:
        return MeCab.Tagger(*args).parse(content)
    else:
        return run_mecab_process(content, *args, **kwargs)


def wakati(content):
    return parse(content, '-Owakati')
