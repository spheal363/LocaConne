# 「地域（LOCAL）」×「つながる（CONNECT）」 = ろかこね
地域に関する情報を共有し、ユーザー同士でつながることを目的としたウェブアプリケーションです。  
Flask、Google Cloud API、MySQL、Wikidata、Wikipedia APIを活用して、ユーザーが投稿したテキストや画像から自動的に地名を抽出し、その場所の詳細情報を提供します。

こちらからアクセスできます！👉[ろかこねを試す](https://locaconne.net/timeline)

## さらに詳しく知りたい人向け
<details>
<summary>資料を表示</summary>
  
![第6回_page-0001](https://github.com/user-attachments/assets/10cdee9d-0f72-4407-a8d5-4e29f11329c1)

</details>

---

## 作成環境

- **OS**: Ubuntu 22.04 LTS
- **プログラミング言語**: Python 3.10
- **Webフレームワーク**: Flask
- **データベース**: MySQL 8.0
- **自然言語処理ライブラリ**: MeCab (NEologd 辞書使用), unidic-lite
- **API**:
  - Google Cloud Vision API
  - Google Cloud Storage
  - Wikidata SPARQL API
  - Wikipedia API
- **その他のライブラリ**:
  - requests
  - hashlib
  - SPARQLWrapper
  - datetime
  - subprocess

---

## プロジェクト概要

### 機能
1. **ユーザー投稿**
   - テキストと画像を投稿可能
   - 投稿内容から自動的に地名を抽出（MeCabを使用）
   - 画像からランドマークの検出（Google Cloud Vision APIを使用）
   - 抽出した地名の情報をWikidataおよびWikipediaから取得し、MySQLデータベースに保存

2. **タイムライン表示**
   - 投稿されたテキスト、画像、地名情報を一覧表示
   - 投稿の詳細ページでは、地名に関連する説明や座標、Wikipediaの概要を表示

3. **地名解析**
   - MeCab（NEologd辞書）を用いた地名の抽出
   - Wikidata SPARQL APIから地名に関連する情報（説明、座標）を取得
   - Wikipedia APIから場所に関する簡単な説明を取得

---

## セットアップ手順

### 1. リポジトリのクローン
```bash
$ git clone <repository-url>
$ cd LocaConne
```

### 2.必要なPythonパッケージのインストール
```sh
pip install Flask
pip install mecab-python3
pip install unidic-lite
pip install google-cloud
pip install google-cloud-vision
pip install google-cloud-storage
pip install mysql-connector-python
pip install SPARQLWrapper
pip install requests
pip install wikipedia
pip install pillow
pip install mysql-connector-python
```

### 3.MeCabとNEologd辞書のインストール
```bash
cd ~
sudo apt update
sudo apt install mecab libmecab-dev mecab-ipadic-utf8
git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git
cd mecab-ipadic-neologd
sudo bin/install-mecab-ipadic-neologd
```
### 4.MySQLデータベースのセットアップ
```sql
CREATE DATABASE locaconne_schema;
USE locaconne_schema;

-- postsテーブル
CREATE TABLE posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255),
    text TEXT,
    image_url VARCHAR(500),
    time DATETIME
);

-- location_detailsテーブル
CREATE TABLE location_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT,
    location VARCHAR(255),
    description TEXT,
    coordinate VARCHAR(100),
    wikipedia_summary TEXT,
    FOREIGN KEY (post_id) REFERENCES posts(id)
);

```

### 5.Google Cloud APIの設定
- Google Cloud Consoleでプロジェクトを作成し、APIを有効化
  - Vision API
  - Cloud Storage
- サービスアカウントキーを取得し、プロジェクトフォルダに配置
  - ファイル名: locaconne.json
 
### 6.Flaskアプリケーションの起動
```bash
$ export GOOGLE_APPLICATION_CREDENTIALS="/path/to/locaconne.json"
$ python app.py
```

ブラウザで以下のURLにアクセスして動作確認を行います。
http://localhost:5000

--- 
## 使用例
1. 投稿フォーム (/post-form)
ユーザーはテキストと画像を投稿できます。
- 例: 「先週、京都に行ってきました！」
2. タイムライン (/timeline)
投稿された内容が時系列で表示されます。
3. 投稿詳細ページ (/post/<post_id>)
投稿内容に関連する地名の説明やWikipediaから取得した概要が表示されます。

