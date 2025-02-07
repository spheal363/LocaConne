import MeCab
from config import NEOLOGD_PATH

def word_verification(text):
    """
    除外ワードチェックの関数
    """
    exclusion_list = ["新開発", "日本", "関東", "関西", "東北", "東", "西", "南", "北"]
    return text not in exclusion_list

def place_extracting(text):
    """
    テキストから地名を抽出する関数
    """
    mecab = MeCab.Tagger(f'-d {NEOLOGD_PATH}')
    node = mecab.parseToNode(text)
    loc_list = []
    
    while node:
        pos = node.feature.split(",")
        if word_verification(node.surface):
            # 固有名詞または一般名詞かつ「地域」や「温泉」を含む場合に抽出
            if len(pos) > 1 and (pos[1] == "固有名詞" or pos[1] == "一般"):
                if pos[2] == "地域" or "温泉" in node.surface:
                    loc_list.append(node.surface)
        node = node.next

    return loc_list
