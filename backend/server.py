# 必要なモジュールのインポート
from flask import Flask, request, jsonify, render_template, redirect
import MeCab, unidic_lite, re, hashlib
from google.cloud import vision, storage
import mysql.connector as mydb
from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime
import requests

# Flaskアプリケーションのセットアップ
app = Flask(__name__)

# Google Cloud Vision APIのクライアント設定
vision_client = vision.ImageAnnotatorClient.from_service_account_file(
    "/home/sdoi/LocaConne/locaconne.json"
)

# Cloud Storageのクライアント設定
storage_client = storage.Client.from_service_account_json(
    "/home/sdoi/LocaConne/locaconne.json"
)
bucket_name = "locaconne_bucket"

# コネクションの作成
conn = mydb.connect(
    host="23.251.151.188", port="3306", user="root", database="locaconne_schema"
)
# コネクションが切れた時に再接続してくれるよう設定
conn.ping(reconnect=True)

# SPARQLエンドポイントの設定
sparql = SPARQLWrapper("https://query.wikidata.org/sparql")


# 除外ワードの設定
# 参考：https://qiita.com/yineleyici/items/73296d4b7491bdb77cd0
def WordVerification(text):
    # 正規表現でカタカナを除外する
    regex = "^[\u30a1-\u30fa\u30fc]+$"
    match = re.match(regex, text)
    if match:
        return False

    # リストに一致するワードを除外する
    elif text in ["新開発", "日本", "関東", "関西", "東北", "東", "西", "南", "北"]:
        return False

    else:
        return True


# 地名だけ抽出する
def PlaceExtracting(text):
    # 形態素解析
    mecab = MeCab.Tagger()
    node = mecab.parseToNode(text)
    locList = []
    while node:
        pos = node.feature.split(",")

        # 除外ワードに引っかからなくてかつ地名であるとき
        if WordVerification(node.surface) and pos[2] == "地名":
            locList.append(node.surface)
        node = node.next

    return locList


# Wikidata APIを使用して地名から場所の情報を取得
def get_location_details(location):
    print(f"Searching for location: {location}")
    
    # Wikidata APIのエンドポイント
    url = "https://www.wikidata.org/w/api.php"
    params = {
        'action': 'wbsearchentities',
        'search': location,
        'language': 'ja',
        'format': 'json',
        'limit': 1
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # HTTPエラーのチェック
        data = response.json()
        
        if 'search' in data and len(data['search']) > 0:
            # 検索結果からQIDを取得
            qid = data['search'][0]['id']
            label = data['search'][0]['label']
            description = data['search'][0].get('description', '')

            # QIDから座標情報を取得
            coordinate = get_coordinates_from_qid(qid)
            
            print(f"Found location: {label}, Description: {description}, Coordinate: {coordinate}")
            return label, description, coordinate
        else:
            print("No location found")
            return None, None, None

    except Exception as e:
        print(f"Error in get_location_details: {e}")
        return None, None, None


# QIDから座標情報を取得
def get_coordinates_from_qid(qid):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(f"""
        SELECT ?coordinate WHERE {{
            wd:{qid} wdt:P625 ?coordinate.
        }}
        LIMIT 1
    """)
    sparql.setReturnFormat(JSON)
    
    try:
        results = sparql.query().convert()
        if results["results"]["bindings"]:
            coordinate = results["results"]["bindings"][0]["coordinate"]["value"]
            return coordinate
    except Exception as e:
        print(f"SPARQL query failed: {e}")
    
    return None


# 地名の情報をlocation_detailsテーブルに保存する関数
def save_location_details(post_id, location):
    place_label, description, coordinate = get_location_details(location)  # 返り値が3つであることを考慮
    if place_label:
        try:
            cursor = conn.cursor()
            sql = "INSERT INTO location_details (post_id, location, description, coordinate) VALUES (%s, %s, %s, %s)"  # 座標も保存するようにクエリを修正
            val = (post_id, place_label, description, coordinate)
            cursor.execute(sql, val)
            conn.commit()
            cursor.close()
            print(f"Location details saved for post ID {post_id}")
        except mydb.Error as e:
            print(f"Error saving location details: {e}")



# 投稿フォーム表示用のエンドポイント
@app.route("/post-form", methods=["GET"])
def post_form():
    return render_template("post.html")


# ユーザー投稿用のエンドポイント
@app.route("/post", methods=["POST"])
def post_content():
    data = request.form
    username = data.get("username", "")
    text = data.get("text", "")
    image = request.files.get("image")
    image_url = ""

    # 画像をCloud Storageにアップロード
    if image:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hash_input = f"{image.filename}_{current_time}"
        hashed_filename = hashlib.sha256(hash_input.encode()).hexdigest()

        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(hashed_filename)
        blob.upload_from_file(image, content_type=image.content_type)
        image_url = f"https://storage.googleapis.com/{bucket_name}/{hashed_filename}"

    # 場所名の抽出（自然言語処理）
    locations = PlaceExtracting(text)

    # 画像解析によるランドマーク検出
    if image_url:
        try:
            vision_image = vision.Image()
            vision_image.source.image_uri = image_url
            image_context = vision.ImageContext(language_hints=["ja"])
            response = vision_client.landmark_detection(
                image=vision_image, image_context=image_context
            )
            if not response.error.message and response.landmark_annotations:
                landmark = response.landmark_annotations[0].description
        except Exception as e:
            print(f"Error in landmark detection: {e}")

    # データベースに投稿を保存
    cursor = conn.cursor()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = "INSERT INTO posts (username, text, image_url, time) VALUES (%s, %s, %s, %s)"
    val = (username, text, image_url, current_time)
    cursor.execute(sql, val)
    conn.commit()
    post_id = cursor.lastrowid  # 保存した投稿のIDを取得

    # 地名情報を取得して保存
    save_location_details(post_id, landmark)

    return jsonify({"status": "success"})


# タイムライン表示用のエンドポイント
@app.route("/timeline", methods=["GET"])
def get_timeline():
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT username, text, image_url, time FROM posts ORDER BY time DESC"
    )
    posts = cursor.fetchall()
    return render_template("timeline.html", posts=posts)


# リダイレクト
@app.route("/")
def main():
    return redirect("/timeline")


# メイン関数
if __name__ == "__main__":
    app.run(debug=True)
