import wikipedia
from google.cloud import vision, storage
from SPARQLWrapper import SPARQLWrapper, JSON

# Wikipediaの言語設定（日本語）
wikipedia.set_lang("ja")

# Google Cloud Vision APIのクライアント設定
VISION_CLIENT = vision.ImageAnnotatorClient.from_service_account_file(
    "./locaconne.json"
)

# Cloud Storageのクライアント設定
STORAGE_CLIENT = storage.Client.from_service_account_json(
    "./locaconne.json"
)
BUCKET_NAME = "locaconne_bucket"

# SPARQLエンドポイントの設定
SPARQL = SPARQLWrapper("https://query.wikidata.org/sparql")

# MeCab用NEologd辞書のパス
NEOLOGD_PATH = "/usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd"
