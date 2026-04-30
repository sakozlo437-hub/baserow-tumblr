import requests
import os
import json
import re
import time
from requests_oauthlib import OAuth1

print("=" * 60)
print("🚀 AI CONTENT GENERATOR + Tumblr Poster")
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

API_URL = f"https://api.baserow.io/api/database/rows/table/{TABLE_ID}/"
HEADERS = {"Authorization": f"Token {TOKEN}", "Content-Type": "application/json"}

# ID полей из твоей таблицы Baserow
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
    "Tumblr post URL": 8317885  # Новая колонка для ссылки на пост
}

def call_ai(start_text):
    """Отправляет запрос в Gemma 4 через OpenRouter"""
    print(f"\n🤖 Отправляю в Gemma 4: {start_text[:80]}...")
    
    prompt = f"""Ты SEO-специалист для fashion-ритейлера. Создай контент для товара: "{start_text}"

Ответь ТОЛЬКО в формате JSON (без пояснений):
{{
    "title": "SEO заголовок до 65 символов с 1-2 эмодзи",
    "body_text": "2-3 эмоциональных предложения в стиле 'кусочек лета', про посадку и настроение",
    "slug": "транслит-латиницей-через-дефисы",
    "tags": "5-8 тегов через запятую на английском"
}}"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "google/gemma-4-31b-it:free",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=60
        )
        
        print(f"📡 OpenRouter ответ: {response.status_code}")
        
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            print(f"✅ Получен ответ от ИИ")
            
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "title": result.get("title", "")[:70],
                    "body_text": result.get("body_text", ""),
                    "slug": result.get("slug", "").lower().replace("_", "-"),
                    "tags": result.get("tags", "")
                }
            else:
                raise Exception("JSON не найден")
        else:
            print(f"⚠️ Ошибка API: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
    
    print("⚠️ Использую локальную заглушку")
    return {
        "title": f"✨ {start_text[:50]}",
        "body_text": f"Feeling like a little piece of summer! ☀️\n\n{start_text[:100]}...",
        "slug": re.sub(r'[^a-z0-9-]', '-', start_text[:50].lower().replace(' ', '-')),
        "tags": "summer, beach, fashion, swimwear"
    }

def download_image(image_url):
    """Скачивает изображение по URL"""
    try:
        print(f"📸 Скачиваю: {image_url[:80]}...")
        response = requests.get(image_url, timeout=30)
        
        if response.status_code == 200:
            ext = 'jpg'
            if 'png' in response.headers.get('content-type', ''):
                ext = 'png'
            elif 'webp' in response.headers.get('content-type', ''):
                ext = 'webp'
            filename = f"image_{int(time.time())}_{hash(image_url) % 10000}.{ext}"
            print(f"✅ Скачано: {filename} ({len(response.content)} bytes)")
            return filename, response.content
        else:
            print(f"⚠️ Ошибка скачивания: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        return None, None

def upload_image_to_baserow(row_id, filename, image_data):
    """Загружает изображение в Baserow (поле Image data)"""
    try:
        print(f"📤 Загружаю изображение в Baserow...")
        upload_url = "https://api.baserow.io/api/user-files/upload-file/"
        files = {'file': (filename, image_data, 'image/jpeg')}
        
        response = requests.post(
            upload_url,
            headers={"Authorization": f"Token {TOKEN}"},
            files=files
        )
        
        if response.status_code != 200:
            print(f"⚠️ Ошибка загрузки: {response.status_code}")
            return None
        
        file_info = response.json()
        if isinstance(file_info, list):
            file_data = file_info[0]
        else:
            file_data = file_info
        
        # Обновляем поле Image data
        update_data = {f"field_{FIELD_IDS['Image data']}": [file_data]}
        patch_resp = requests.patch(f"{API_URL}{row_id}/", headers=HEADERS, json=update_data)
        
        if patch_resp.status_code == 200:
            print("✅ Image data обновлён")
            return file_data.get("url")
        else:
            print(f"⚠️ Ошибка обновления: {patch_resp.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        return None

def post_to_tumblr(title, body, tags, slug, link, image_url):
    """Отправляет пост в Tumblr"""
    if not all([TUMBLR_CONSUMER_KEY, TUMBLR_ACCESS_TOKEN, TUMBLR_BLOG_NAME]):
        print("⚠️ Tumblr секреты не настроены, пропускаем публикацию")
        return None
    
    print(f"\n📝 Отправляю пост в Tumblr...")
    
    # Формируем HTML тело поста с изображением и ссылкой
    html_body = f"""
    <div style="max-width: 540px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <h2>{title}</h2>
        <img src="{image_url}" style="width:100%; border-radius:12px; margin-bottom:16px;">
        <p>{body}</p>
        <p style="margin-top:16px;">
            <a href="{link}" style="background:#000; color:#fff; padding:10px 20px; border-radius:30px; text-decoration:none; display:inline-block;">🛍️ Buy Now</a>
        </p>
    </div>
    """
    
    # OAuth 1.0 авторизация
    auth = OAuth1(
        TUMBLR_CONSUMER_KEY,
        client_secret=TUMBLR_CONSUMER_SECRET,
        resource_owner_key=TUMBLR_ACCESS_TOKEN,
        resource_owner_secret=TUMBLR_ACCESS_SECRET
    )
    
    url = f"https://api.tumblr.com/v2/blog/{TUMBLR_BLOG_NAME}/post"
    
    data = {
        "type": "text",
        "title": title[:100],
        "body": html_body,
        "tags": tags,
        "slug": slug,
        "state": "published"
    }
    
    try:
        response = requests.post(url, auth=auth, data=data)
        print(f"📡 Tumblr ответ: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            post_url = result["response"]["post_url"]
            print(f"✅ Пост опубликован: {post_url}")
            return post_url
        else:
            print(f"⚠️ Ошибка Tumblr: {response.text[:300]}")
            return None
    except Exception as e:
        print(f"⚠️ Ошибка при отправке в Tumblr: {e}")
        return None

# ========== ОСНОВНАЯ ЛОГИКА ==========

def main():
    # 1. Поиск строки с пустым Status
    print("\n📡 Поиск строки с пустым Status...")
    resp = requests.get(API_URL, headers=HEADERS, params={"size": 10})
    
    if resp.status_code != 200:
        print(f"❌ Ошибка API Baserow: {resp.status_code}")
        print(f"Ответ: {resp.text[:200]}")
        exit(1)
    
    rows = resp.json().get("results", [])
    print(f"Найдено строк: {len(rows)}")
    
    target = None
    for row in rows:
        status_value = row.get(f"field_{FIELD_IDS['Status']}")
        print(f"  Row {row['id']}: Status = '{status_value}'")
        if status_value in (None, ""):
            target = row
            print(f"  👉 Будет обработана")
            break
    
    if not target:
        print("❌ Нет строк для обработки")
        exit(0)
    
    # 2. Получаем данные из строки
    start_text = target.get(f"field_{FIELD_IDS['Start text']}", "")
    start_image_url = target.get(f"field_{FIELD_IDS['Start image']}", "")
    link = target.get(f"field_{FIELD_IDS['Link']}", "")
    
    print(f"\n📝 Start text: {start_text[:100]}...")
    print(f"🖼️ Start image: {start_image_url[:80]}...")
    
    # 3. Генерация контента через ИИ
    ai_data = call_ai(start_text)
    
    print(f"\n📊 Результаты ИИ:")
    print(f"   Title: {ai_data.get('title', '')[:60]}")
    print(f"   Body: {ai_data.get('body_text', '')[:80]}...")
    print(f"   Slug: {ai_data.get('slug', '')}")
    print(f"   Tags: {ai_data.get('tags', '')}")
    
    # 4. Обновляем текстовые поля и статус
    print(f"\n📝 Обновляю текстовые поля в Baserow...")
    
    update_data = {
        f"field_{FIELD_IDS['Title']}": ai_data.get("title", ""),
        f"field_{FIELD_IDS['Body text']}": ai_data.get("body_text", ""),
        f"field_{FIELD_IDS['Slug']}": ai_data.get("slug", ""),
        f"field_{FIELD_IDS['Tags']}": ai_data.get("tags", ""),
        f"field_{FIELD_IDS['Status']}": "выполнено"
    }
    
    patch_resp = requests.patch(f"{API_URL}{target['id']}/", headers=HEADERS, json=update_data)
    
    if patch_resp.status_code != 200:
        print(f"❌ Ошибка обновления: {patch_resp.text}")
        exit(1)
    
    print("✅ Текстовые поля обновлены")
    
    # 5. Обработка изображения
    print(f"\n📸 Обработка изображения...")
    image_url_for_tumblr = None
    
    if start_image_url:
        filename, image_data = download_image(start_image_url)
        if image_data:
            image_url_for_tumblr = upload_image_to_baserow(target['id'], filename, image_data)
            if image_url_for_tumblr:
                print(f"✅ Изображение загружено в Baserow")
            else:
                print("⚠️ Не удалось загрузить изображение в Baserow")
        else:
            print("⚠️ Изображение не скачано")
    else:
        print("⚠️ Нет URL изображения в поле Start image")
    
    # 6. Отправка в Tumblr
    tumblr_post_url = post_to_tumblr(
        title=ai_data.get("title", ""),
        body=ai_data.get("body_text", ""),
        tags=ai_data.get("tags", ""),
        slug=ai_data.get("slug", ""),
        link=link,
        image_url=image_url_for_tumblr or start_image_url
    )
    
    # 7. Сохраняем URL поста в отдельную колонку
    if tumblr_post_url:
        update_tumblr = {f"field_{FIELD_IDS['Tumblr post URL']}": tumblr_post_url}
        tumblr_resp = requests.patch(f"{API_URL}{target['id']}/", headers=HEADERS, json=update_tumblr)
        if tumblr_resp.status_code == 200:
            print("✅ URL поста сохранён в колонку Tumblr post URL")
        else:
            print(f"⚠️ Ошибка сохранения URL: {tumblr_resp.status_code}")
    else:
        print("⚠️ Пост не опубликован, URL не сохранён")
    
    print("\n" + "=" * 60)
    print("🏁 ВСЁ ГОТОВО!")
    print("=" * 60)

if __name__ == "__main__":
    main()
