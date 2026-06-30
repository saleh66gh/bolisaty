import arabic_reshaper
from bidi.algorithm import get_display


def ar(text):
    if text is None:
        return ""
    reshaped_text = arabic_reshaper.reshape(str(text))
    return get_display(reshaped_text)