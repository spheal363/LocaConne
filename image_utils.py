import hashlib
import io
import random
import requests
from PIL import Image
from config import VISION_CLIENT, STORAGE_CLIENT, BUCKET_NAME

def detect_landmark(image_url):
    """
    画像解析によりランドマークを検出する関数
    """
    try:
        from google.cloud import vision  # 既にVISION_CLIENTを利用
        vision_image = vision.Image()
        vision_image.source.image_uri = image_url
        image_context = vision.ImageContext(language_hints=["ja"])
        response = VISION_CLIENT.landmark_detection(
            image=vision_image, image_context=image_context
        )
        if not response.error.message and response.landmark_annotations:
            return response.landmark_annotations[0].description
    except Exception as e:
        print(f"Error in landmark detection: {e}")
    return None

def modify_image(image_url):
    """
    画像サイズを変更し、Cloud Storageに再アップロードする関数
    """
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        image_data = response.content

        # 画像を開く
        image = Image.open(io.BytesIO(image_data))
        original_width, original_height = image.size
        new_width = random.randint(640, original_width)
        new_height = random.randint(480, original_height)
        size = (new_width, new_height)

        # 画像のリサイズ
        image = image.resize(size, Image.LANCZOS)

        # 新しいファイル名の生成
        new_filename = f"modified_{hashlib.sha256(image_data).hexdigest()}.jpg"

        # Cloud Storageへアップロード
        bucket = STORAGE_CLIENT.bucket(BUCKET_NAME)
        blob = bucket.blob(new_filename)
        image_byte_array = io.BytesIO()
        image.save(image_byte_array, format='JPEG')
        blob.upload_from_string(image_byte_array.getvalue(), content_type='image/jpeg')

        # 新しい画像URLの生成
        new_image_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{new_filename}"
        return new_image_url

    except Exception as e:
        print(f"Error in modify_image: {e}")
        return None
