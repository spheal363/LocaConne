# 必要なモジュールのインポート
from flask import Flask, request, jsonify, render_template, redirect
import spacy
from google.cloud import vision, storage
import mysql.connector as mydb
from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime  # 追加


# Flaskアプリケーションのセットアップ
app = Flask(__name__)


# spaCyのモデル読み込み
nlp: spacy.Language = spacy.load('ja_ginza')

# Google Cloud Vision APIのクライアント設定
vision_client = vision.ImageAnnotatorClient()

# Cloud Storageのクライアント設定
storage_client = storage.Client()
bucket_name = "your-cloud-storage-bucket-name"

# コネクションの作成
conn = mydb.connect(
    host='23.251.151.188',
    port='3306',
    user='root',
    database='locaconne_schema'
)
# コネクションが切れた時に再接続してくれるよう設定
conn.ping(reconnect=True)

# SPARQLエンドポイントの設定
sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

# 投稿フォーム表示用のエンドポイント
@app.route("/post-form", methods=['GET'])
def post_form():
    return render_template("post.html")

# ユーザー投稿用のエンドポイント
@app.route('/post', methods=['POST'])
def post_content():
    data = request.form
    text = data.get('text', '')
    image = request.files.get('image')
    image_url = ""

    # 画像をCloud Storageにアップロード
    if image:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(image.filename)
        blob.upload_from_file(image)
        image_url = f"https://storage.googleapis.com/{bucket_name}/{image.filename}"

    # 場所名の抽出（自然言語処理）
    doc = nlp(text)
    locations = [ent.text for ent in doc.ents if ent.label_ == "GPE"]

    # 画像解析によるランドマーク検出
    landmarks = []
    if image_url:
        vision_image = vision.Image()
        vision_image.source.image_uri = image_url
        response = vision_client.landmark_detection(image=vision_image)
        for landmark in response.landmark_annotations:
            landmarks.append(landmark.description)

    # 抽出した場所情報をもとにWikidataから詳細を取得
    details = []
    for location in locations + landmarks:
        sparql.setQuery(f"""
        SELECT ?item ?itemLabel ?description
        WHERE {{
          ?item wdt:P31/wdt:P279* wd:Q515;  # instance of city or town
                rdfs:label "{location}"@ja.
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" }}
        }}
        LIMIT 1
        """
        )
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            details.append({
                "name": result["itemLabel"]["value"],
                "description": result.get("description", {}).get("value", "No description available")
            })

    # データベースに投稿を保存
    cursor = conn.cursor()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 現在時刻を取得
    sql = "INSERT INTO posts (text, image_url, time) VALUES (%s, %s, %s)"
    val = (text, image_url, current_time)
    cursor.execute(sql, val)
    conn.commit()

    return jsonify({"status": "success", "details": details})

# タイムライン表示用のエンドポイント
@app.route("/timeline", methods=['GET'])
def get_timeline():
    # DB操作用にカーソルを作成
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM posts ORDER BY time DESC")
    # 全てのデータを取得
    posts = cursor.fetchall()
    # タイムラインページをレンダリング
    return render_template("timeline.html", posts=posts)

# リダイレクト
@app.route("/")
def main():
    return redirect("/timeline")

# メイン関数
if __name__ == '__main__':
    app.run(debug=True)
