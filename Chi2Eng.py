from googletrans import Translator

def translate_to_english(text):
    translator = Translator()
    result = translator.translate(text, src='zh-cn', dest='en')  # 支援自動識別繁簡體
    return result.text

# 判斷是否包含中文的函數
def contains_chinese(text):
    return any('\u4e00' <= char <= '\u9fff' for char in text)