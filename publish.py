import requests
import os
import json
import re
import time
import pytumblr

print("=" * 60)
print("🚀 AI CONTENT GENERATOR + Tumblr Poster (pytumblr)")
print("=" * 60)

# Диагностика секретов
print("\n🔍 DIAGNOSTICS:")
print(f"BASEROW_TOKEN: {'✅' if os.environ.get('BASEROW_TOKEN') else '❌'}")
print(f"BASEROW_TABLE_ID: {'✅' if os.environ.get('BASEROW_TABLE_ID') else '❌'}")
print(f"OPENROUTER_API_KEY: {'✅' if os.environ.get('OPENROUTER_API_KEY') else '❌'}")
print(f"TUMBLR_CONSUMER_KEY: {'✅' if os.environ.get('TUMBLR_CONSUMER_KEY') else '❌'}")
print(f"TUMBLR_ACCESS_TOKEN: {'✅' if os.environ.get('TUMBLR_ACCESS_TOKEN') else '❌'}")
print(f"TUMBLR_BLOG_NAME: {'✅' if os.environ.get('TUMBLR_BLOG_NAME') else '❌'}")

TOKEN = os.environ.get("BASEROW_TOKEN")
TABLE_ID = os.environ.get("BASEROW_TABLE_ID")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

TUMBLR_CONSUMER_KEY = os.environ.get("TUMBLR_CONSUMER_KEY")
TUMBLR_CONSUMER_SECRET = os.environ.get("TUMBLR_CONSUMER_SECRET")
TUMBLR_ACCESS_TOKEN = os.environ.get("TUMBLR_ACCESS_TOKEN")
TUMBLR_ACCESS_SECRET = os.environ.get("TUMBLR_ACCESS_SECRET")
TUMBLR_BLOG_NAME = os.environ.get("TUMBLR_BLOG_NAME")

if not all([TOKEN, TABLE_ID, OPENROUTER_API_KEY]):
    print("\n❌ Ошибка: не все секреты Baserow/OpenRouter настроены")
    exit(1)

# Инициализация Tumblr клиента
tumblr_client = None
if all([TUMBLR_CONSUMER_KEY, TUMBLR_CONSUMER_SECRET, TUMBLR_ACCESS_TOKEN, TUMBLR_ACCESS_SECRET]):
    tumblr_client = pytumblr.TumblrRestClient(
        TUMBLR_CONSUMER_KEY,
        TUMBLR_CONSUMER_SECRET,
        TUMBLR_ACCESS_TOKEN,
        TUMBLR_ACCESS_SECRET
    )
    print("\n✅ Tumblr клиент инициализирован")
    
    # Проверяем подключение
    try:
        info = tumblr_client.info()
        if info.get('blog'):
            print(f"✅ Подключено к блогу: {info['blog']['title']}")
            print(f"   Постов: {info['blog']['posts']}")
        else:
            print(f"⚠️ Ответ: {info}")
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")

API_URL = f"https://api.baserow.io/api/database/rows/table/{TABLE_ID}/"
HEADERS = {"Authorization": f"Token {TOKEN}", "Content-Type": "application/json"}

# ID полей
FIELD_IDS = {
    "Start text": 8259553,
    "Start image": 8259554,
    "Title": 8259555,
    "Body text": 8259556,
    "Image data": 8259557,
    "Body link": 8259558,
    "Link": 8259559,
    "Slug": 8259560,
    "Tags": 8259561,
    "Status": 8259562,
    "Tumblr post URL": 8317885
}

def call_ai(start_text):
    """Отправляет запрос в Gemma 4 через OpenRouter"""
    print(f"\n🤖 Отправляю в Gemma 4: {start_text[:80]}...")
    
    prompt = f"""Ты SEO-специалист для fashion-ритейлера. Создай контент для товара: "{start_text}"

Ответь ТОЛЬКО в формате JSON:
{{"title":"...", "body_text":"...", "slug":"...", "tags":"..."}}
title: до 65 символов с эмодзи
body_text: 2-3 эмоциональных предложения
slug: латиница-дефисы
tags: 5 тегов через запятую"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "google/gemma-4-31b-it:free",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=60
        )
        
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "title": result.get("title", "")[:70],
                    "body_text": result.get("body_text", ""),
                    "slug": result.get("slug", "").lower().replace("_", "-"),
                    "tags": result.get("tags", "")
                }
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
    
    # Заглушка
    return {
        "title": f"✨ {start_text[:50]}",
        "body_text": f"Feeling like a little piece of summer! ☀️\n\n{start_text[:100]}...",
        "slug": re.sub(r'[^a-z0-9-]', '-', start_text[:50].lower().replace(' ', '-')),
        "tags": "summer, beach, fashion, swimwear"
    }

def download_image(image_url):
    """Скачивает изображение"""
    try:
        response = requests.get(image_url, timeout=30)
        if response.status_code == 200:
            filename = f"image_{int(time.time())}.jpg"
            return filename, response.content
        return None, None
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        return None, None

def upload_image_to_baserow(row_id, filename, image_data):
    """Загружает изображение в Baserow"""
    try:
        upload_url = "https://api.baserow.io/api/user-files/upload-file/"
        files = {'file': (filename, image_data, 'image/jpeg')}
        
        response = requests.post(upload_url, headers={"Authorization": f"Token {TOKEN}"}, files=files)
        
        if response.status_code != 200:
            return None
        
        file_info = response.json()
        if isinstance(file_info, list):
            file_data = file_info[0]
        else:
            file_data = file_info
        
        update_data = {f"field_{FIELD_IDS['Image data']}": [file_data]}
        requests.patch(f"{API_URL}{row_id}/", headers=HEADERS, json=update_data)
        return file_data.get("url")
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        return None

def post_to_tumblr(title, body, tags, image_url, link):
    """Отправляет пост в Tumblr через pytumblr"""
    if not tumblr_client:
        return None
    
    # Получаем имя блога без .tumblr.com
    blog_name = TUMBLR_BLOG_NAME.replace("https://", "").replace("http://", "").strip("/")
    if blog_name.endswith('.tumblr.com'):
        blog_name = blog_name.replace('.tumblr.com', '')
    
    # Формируем HTML
    html_body = f"""
    <div style="max-width:540px;margin:0 auto;">
        <h2>{title}</h2>
        <img src="{image_url}" style="width:100%;border-radius:12px;margin-bottom:16px;">
        <p>{body}</p>
        <p><a href="{link}" style="background:#000;color:#fff;padding:10px 20px;border-radius:30px;text-decoration:none;">🛍️ Buy Now</a></p>
    </div>
    """
    
    try:
        result = tumblr_client.create_text(
            blog_name,
            title=title[:100],
            body=html_body,
            tags=tags[:200],
            slug=title[:50].lower().replace(' ', '-'),
            state="published"
        )
        
        if result and result.get('id'):
            post_url = f"https://{blog_name}.tumblr.com/post/{result['id']}"
            return post_url
        return None
    except Exception as e:
        print(f"⚠️ Ошибка Tumblr: {e}")
        return None

# ========== ОСНОВНАЯ ЛОГИКА ==========

def main():
    print("\n📡 Поиск строки с пустым Status...")
    resp = requests.get(API_URL, headers=HEADERS, params={"size": 10})
    
    if resp.status_code != 200:
        print(f"❌ Ошибка: {resp.status_code}")
        exit(1)
    
    rows = resp.json().get("results", [])
    
    target = None
    for row in rows:
        if row.get(f"field_{FIELD_IDS['Status']}") in (None, ""):
            target = row
            break
    
    if not target:
        print("❌ Нет строк для обработки")
        exit(0)
    
    start_text = target.get(f"field_{FIELD_IDS['Start text']}", "")
    start_image_url = target.get(f"field_{FIELD_IDS['Start image']}", "")
    link = target.get(f"field_{FIELD_IDS['Link']}", "")
    
    # Генерация контента
    ai_data = call_ai(start_text)
    
    # Обновляем текстовые поля
    update_data = {
        f"field_{FIELD_IDS['Title']}": ai_data.get("title", ""),
        f"field_{FIELD_IDS['Body text']}": ai_data.get("body_text", ""),
        f"field_{FIELD_IDS['Slug']}": ai_data.get("slug", ""),
        f"field_{FIELD_IDS['Tags']}": ai_data.get("tags", ""),
        f"field_{FIELD_IDS['Status']}": "выполнено"
    }
    
    requests.patch(f"{API_URL}{target['id']}/", headers=HEADERS, json=update_data)
    
    # Обработка изображения
    image_url_for_post = start_image_url
    if start_image_url:
        filename, image_data = download_image(start_image_url)
        if image_data:
            uploaded_url = upload_image_to_baserow(target['id'], filename, image_data)
            if uploaded_url:
                image_url_for_post = uploaded_url
    
    # Отправка в Tumblr
    if tumblr_client:
        post_url = post_to_tumblr(
            title=ai_data.get("title", ""),
            body=ai_data.get("body_text", ""),
            tags=ai_data.get("tags", ""),
            image_url=image_url_for_post,
            link=link
        )
        
        if post_url:
            update_tumblr = {f"field_{FIELD_IDS['Tumblr post URL']}": post_url}
            requests.patch(f"{API_URL}{target['id']}/", headers=HEADERS, json=update_tumblr)
            
            update_status = {f"field_{FIELD_IDS['Status']}": "размещено"}
            requests.patch(f"{API_URL}{target['id']}/", headers=HEADERS, json=update_status)
            print(f"✅ Пост опубликован: {post_url}")

if __name__ == "__main__":
    main()
