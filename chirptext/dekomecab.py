import os
import platform
import subprocess

# Try to use mecab-python3 if it's available
MECAB_PYTHON3 = False

try:
    import MeCab
    Mecab.Tagger().parse("Pythonが好きです。")
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
        else:
            MECAB_LOC = "mecab"
    except:
        pass


def run_mecab_process(content, *args, **kwargs):
    ''' Use subprocess to run mecab '''
    encoding = 'utf-8' if 'encoding' not in kwargs else  kwargs['encoding']
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
    if MECAB_PYTHON3:
        return MeCab.Tagger(*args).parse(content)
    else:
        return run_mecab_process(content, *args, **kwargs)


def wakati(content):
    return parse(content, '-Owakati')