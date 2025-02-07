from flask import request, jsonify, render_template, redirect
from datetime import datetime
import hashlib

from __init__ import app
from config import STORAGE_CLIENT, BUCKET_NAME
from db import create_mysql_connection # MySQLへの接続を管理する関数
import utils # テキストから地名を抽出する関数
import wikidata_utils # Wikidataから地名の詳細情報を取得する関数
import image_utils # 画像解析（ランドマーク検出）を行う関数

# 投稿フォームの表示
@app.route("/post-form", methods=["GET"])
def post_form():
    return render_template("post.html")

# 投稿内容の受け取りと処理
@app.route("/post", methods=["POST"])
def post_content():
    # フォームデータの取得
    data = request.form
    username = data.get("username", "")
    text = data.get("text", "")
    image = request.files.get("image")
    image_url = ""
    original_image_url = ""

    # 画像がアップロードされた場合、Cloud Storageへ保存
    if image:
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hash_input = f"{image.filename}_{current_time_str}"
        hashed_filename = hashlib.sha256(hash_input.encode()).hexdigest()
        bucket = STORAGE_CLIENT.bucket(BUCKET_NAME)
        blob = bucket.blob(hashed_filename)
        blob.upload_from_file(image, content_type=image.content_type)
        image_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{hashed_filename}"
        original_image_url = image_url  # オリジナル画像のURL

    # テキストから地名を抽出（MeCab）
    locations = utils.place_extracting(text)
    print(locations)

    # 画像解析でランドマーク検出（最大3回試行）
    landmark = None
    for attempt in range(3):
        if image_url:
            landmark = image_utils.detect_landmark(image_url)
            if landmark:
                break
            # ランドマークが検出できなければ画像を加工して再試行
            image_url = image_utils.modify_image(image_url)

    # 投稿内容をデータベースに保存
    conn = create_mysql_connection()
    cursor = conn.cursor()
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = "INSERT INTO posts (username, text, image_url, time) VALUES (%s, %s, %s, %s)"
    val = (username, text, original_image_url, current_time_str)
    cursor.execute(sql, val)
    conn.commit()
    post_id = cursor.lastrowid  # 登録された投稿ID
    cursor.close()
    conn.close()

    # 画像解析とテキスト抽出の結果から地名を決定
    selected_location = None
    if landmark and locations:
        selected_location = landmark  # 両方ある場合は画像解析結果を優先
    elif locations:
        selected_location = locations[0]
    elif landmark:
        selected_location = landmark

    if selected_location:
        wikidata_utils.save_location_details(post_id, selected_location)
    else:
        print("No location information available to save.")
    
    return jsonify({"status": "success"})

# タイムラインの取得
@app.route("/timeline", methods=["GET"])
def get_timeline():
    conn = create_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT p.id, p.username, p.text, p.image_url, p.time, ld.wikipedia_summary
        FROM posts p
        LEFT JOIN location_details ld ON p.id = ld.post_id
        ORDER BY p.time DESC
        """
    )
    posts = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("timeline.html", posts=posts)

# 投稿詳細ページ
@app.route('/post/<int:post_id>', methods=['GET'])
def post_details(post_id):
    conn = create_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    # 投稿内容の取得
    cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
    post = cursor.fetchone()
    # 地名詳細の取得
    cursor.execute("""
        SELECT description, coordinate, wikipedia_summary
        FROM location_details WHERE post_id = %s
    """, (post_id,))
    location = cursor.fetchone()
    cursor.close()
    conn.close()
    description = location['description'] if location else None
    coordinate = location['coordinate'] if location else None
    wikipedia_summary = location['wikipedia_summary'] if location else None
    return render_template(
        'details.html',
        post=post,
        description=description,
        coordinate=coordinate,
        wikipedia_summary=wikipedia_summary
    )

@app.route("/")
def main():
    return redirect("/timeline")

if __name__ == "__main__":
    app.run(debug=True)