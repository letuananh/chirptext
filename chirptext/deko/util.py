# -*- coding: utf-8 -*-

from .. import texttaglib as ttl

# reference: https://en.wikipedia.org/wiki/Hiragana_%28Unicode_block%29
# U+304x 		ぁ 	あ 	ぃ 	い 	ぅ 	う 	ぇ 	え 	ぉ 	お 	か 	が 	き 	ぎ 	く
# U+305x 	ぐ 	け 	げ 	こ 	ご 	さ 	ざ 	し 	じ 	す 	ず 	せ 	ぜ 	そ 	ぞ 	た
# U+306x 	だ 	ち 	ぢ 	っ 	つ 	づ 	て 	で 	と 	ど 	な 	に 	ぬ 	ね 	の 	は
# U+307x 	ば 	ぱ 	ひ 	び 	ぴ 	ふ 	ぶ 	ぷ 	へ 	べ 	ぺ 	ほ 	ぼ 	ぽ 	ま 	み
# U+308x 	む 	め 	も 	ゃ 	や 	ゅ 	ゆ 	ょ 	よ 	ら 	り 	る 	れ 	ろ 	ゎ 	わ
# U+309x 	ゐ 	ゑ 	を 	ん 	ゔ 	ゕ 	ゖ 			゙ 	゚ 	゛ 	゜ 	ゝ 	ゞ 	ゟ

HIRAGANA = 'ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんゔゕゖ゙゚゛゜ゝゞゟ'

# reference: https://en.wikipedia.org/wiki/Katakana_%28Unicode_block%29
# U+30Ax 	゠ 	ァ 	ア 	ィ 	イ 	ゥ 	ウ 	ェ 	エ 	ォ 	オ 	カ 	ガ 	キ 	ギ 	ク
# U+30Bx 	グ 	ケ 	ゲ 	コ 	ゴ 	サ 	ザ 	シ 	ジ 	ス 	ズ 	セ 	ゼ 	ソ 	ゾ 	タ
# U+30Cx 	ダ 	チ 	ヂ 	ッ 	ツ 	ヅ 	テ 	デ 	ト 	ド 	ナ 	ニ 	ヌ 	ネ 	ノ 	ハ
# U+30Dx 	バ 	パ 	ヒ 	ビ 	ピ 	フ 	ブ 	プ 	ヘ 	ベ 	ペ 	ホ 	ボ 	ポ 	マ 	ミ
# U+30Ex 	ム 	メ 	モ 	ャ 	ヤ 	ュ 	ユ 	ョ 	ヨ 	ラ 	リ 	ル 	レ 	ロ 	ヮ 	ワ
# U+30Fx 	ヰ 	ヱ 	ヲ 	ン 	ヴ 	ヵ 	ヶ 	ヷ 	ヸ 	ヹ 	ヺ 	・ 	ー 	ヽ 	ヾ 	ヿ
KATAKANA = '゠ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶヷヸヹヺ・ーヽヾヿ'
KATA2HIRA_TRANS = str.maketrans(KATAKANA[1:87], HIRAGANA[:86])


def simple_kata2hira(input_str):
    return input_str.translate(KATA2HIRA_TRANS)


try:
    from jaconv import kata2hira
except Exception:
    # if jaconv is not available, use built-in method
    kata2hira = simple_kata2hira


def is_kana(text):
    """ Check if a text if written in kana only (hiragana & katakana)
    if text is empty then return True
    """
    if text is None:
        raise ValueError("text cannot be None")
    for c in text:
        if c not in HIRAGANA and c not in KATAKANA:
            return False
    return True


def _token_need_ruby(token):
    return token.reading and token.reading != token.text and token.reading_hira != token.text


def token_to_ruby(token):
    """ Convert one MeCab's token into HTML """
    if _token_need_ruby(token):
        return f'<ruby><rb>{token.text}</rb><rt>{kata2hira(token.reading)}</rt></ruby>'
    else:
        return token.text


def to_csv(obj):
    if isinstance(obj, ttl.Token):
        row = (obj.text, obj.pos, obj.sc1, obj.sc2, obj.sc3, obj.inf, obj.conj, obj.lemma, obj.reading, obj.pron)
        return '\t'.join(str(c) if c else '*' for c in row)
    if isinstance(obj, ttl.Sentence):
        return '\n'.join(to_csv(token) for token in obj)
    else:
        raise ValueError("Unknown object type ({type(obj)})")


def sent_to_ruby(sent):
    ruby_tokens = []
    for token in sent:
        ruby_tokens.append(token_to_ruby(token))
    ruby_text = ' '.join(ruby_tokens)
    # clean sentence a bit ...
    ruby_text = ruby_text.replace(' 。', '。').replace('「 ', '「').replace(' 」', '」').replace(' 、 ', '、').replace('（ ',
                                                                                                       '（').replace(
        ' ）', '）')
    return ruby_text
