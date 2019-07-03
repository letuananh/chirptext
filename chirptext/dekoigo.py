import logging


__IGO_AVAILABLE = False
__IGO_TAGGER = None


def __try_import_igo(log=False):
    global __IGO_AVAILABLE
    global __IGO_TAGGER
    try:
        from igo.Tagger import Tagger
        __IGO_TAGGER = Tagger()
        __IGO_AVAILABLE = True
    except Exception as e:
        if log:
            logging.getLogger(__name__).warning('igo-python is not installed. run `pip install igo-python` to install.', exc_info=True)
    return __IGO_AVAILABLE


def igo_available():
    ''' Check if igo-python package is installed '''
    return __IGO_AVAILABLE


__try_import_igo()


def parse(content, *args, **kwargs):
    global __IGO_TAGGER
    tokens = __IGO_TAGGER.parse(content)
    # format: same as mecab
    # 表層形,品詞,品詞細分類1,品詞細分類2,品詞細分類3,活用形,活用型,原形,読み,発音
    
