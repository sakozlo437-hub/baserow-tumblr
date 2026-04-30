import requests
import os
import json
import re
import time

print("=" * 60)
print("🚀 AI CONTENT GENERATOR (Gemma 4) + File Upload")
print("=" * 60)

# Диагностика секретов
print("\n🔍 DIAGNOSTICS:")
print(f"BASEROW_TOKEN: {'✅' if os.environ.get('BASEROW_TOKEN') else '❌'}")
print(f"BASEROW_TABLE_ID: {'✅' if os.environ.get('BASEROW_TABLE_ID') else '❌'}")
print(f"OPENROUTER_API_KEY: {'✅' if os.environ.get('OPENROUTER_API_KEY') else '❌'}")

TOKEN = os.environ.get("BASEROW_TOKEN")
TABLE_ID = os.environ.get("BASEROW_TABLE_ID")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

if not TOKEN or not TABLE_ID or not OPENROUTER_API_KEY:
    print("\n❌ Ошибка: не все секреты настроены")
    exit(1)

API_URL = f"https://api.baserow.io/api/database/rows/table/{TABLE_ID}/"
HEADERS = {"Authorization": f"Token {TOKEN}", "Content-Type": "application/json"}

# ID полей из твоей таблицы
FIELD_IDS = {
    "Start text": 8259553,
    "Start image": 8259554,
    "Title": 8259555,
    "Body text": 8259556,
    "Image data": 8259557,  # Теперь тип File
    "Body link": 8259558,
    "Link": 8259559,
    "Slug": 8259560,
    "Tags": 8259561,
    "Status": 8259562
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
}}

Пример: 
{{"title": "🔥 Bohemian Waters Cheeky Bottoms — идеальная посадка", 
"body_text": "☀️ Эти боттомы — любовь с первой примерки! Не врезаются, сидят как влитые. Pure beach happiness ✨",
"slug": "bohemian-waters-cheeky-bottoms-l", 
"tags": "boho swimwear, cheeky bikini, summer vacation, beach outfit"}}"""

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
    
    # Заглушка при ошибке
    print("⚠️ Использую локальную заглушку")
    return {
        "title": f"✨ {start_text[:50]}",
        "body_text": f"Feeling like a little piece of summer! ☀️\n\n{start_text[:100]}...\n\nPerfect fit, nothing digs in, nothing slips — just pure beach happiness! ✨",
        "slug": re.sub(r'[^a-z0-9-]', '-', start_text[:50].lower().replace(' ', '-')),
        "tags": "summer, beach, fashion, swimwear, vacation, style, bikini"
    }

def download_image(image_url):
    """Скачивает изображение по URL"""
    try:
        print(f"📸 Скачиваю изображение: {image_url[:80]}...")
        response = requests.get(image_url, timeout=30)
        
        if response.status_code == 200:
            # Определяем расширение файла
            content_type = response.headers.get('content-type', '')
            ext = 'jpg'
            if 'png' in content_type:
                ext = 'png'
            elif 'webp' in content_type:
                ext = 'webp'
            elif 'gif' in content_type:
                ext = 'gif'
            
            filename = f"image_{int(time.time())}_{hash(image_url) % 10000}.{ext}"
            image_data = response.content
            print(f"✅ Скачано: {filename} ({len(image_data)} bytes)")
            return filename, image_data
        else:
            print(f"⚠️ Не удалось скачать: статус {response.status_code}")
            return None, None
    except Exception as e:
        print(f"⚠️ Ошибка скачивания: {e}")
        return None, None

def upload_image_to_baserow(row_id, filename, image_data):
    """Загружает изображение в поле Image data (тип File) в Baserow"""
    try:
        print(f"📤 Загружаю изображение в Baserow (тип File)...")
        upload_url = "https://api.baserow.io/api/user-files/upload-file/"
        
        files = {'file': (filename, image_data, 'image/jpeg')}
        
        response = requests.post(
            upload_url,
            headers={"Authorization": f"Token {TOKEN}"},
            files=files
        )
        
        if response.status_code == 200:
            file_info = response.json()[0]
            print(f"✅ Изображение загружено на сервер Baserow")
            
            # Обновляем поле Image data (тип File)
            update_data = {f"field_{FIELD_IDS['Image data']}": [file_info]}
            patch_resp = requests.patch(
                f"{API_URL}{row_id}/",
                headers=HEADERS,
                json=update_data
            )
            
            if patch_resp.status_code == 200:
                print("✅ Поле Image data обновлено (файл сохранён в Baserow)")
                return True
            else:
                print(f"⚠️ Ошибка обновления: {patch_resp.status_code}")
                return False
        else:
            print(f"⚠️ Ошибка загрузки файла: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        return False

# ========== ОСНОВНАЯ ЛОГИКА ==========

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

# 2. Получаем данные
start_text = target.get(f"field_{FIELD_IDS['Start text']}", "")
start_image_url = target.get(f"field_{FIELD_IDS['Start image']}", "")

print(f"\n📝 Start text: {start_text[:100]}...")
print(f"🖼️ Start image: {start_image_url[:80]}...")

# 3. Генерация контента через ИИ
ai_data = call_ai(start_text)

print(f"\n📊 Результаты ИИ:")
print(f"   Title: {ai_data.get('title', '')[:60]}")
print(f"   Body: {ai_data.get('body_text', '')[:80]}...")
print(f"   Slug: {ai_data.get('slug', '')}")
print(f"   Tags: {ai_data.get('tags', '')}")

# 4. Обновляем текстовые поля
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

# 5. Обработка изображения (скачиваем и загружаем в Image data как файл)
print(f"\n📸 Обработка изображения...")

if start_image_url:
    filename, image_data = download_image(start_image_url)
    if image_data:
        upload_image_to_baserow(target['id'], filename, image_data)
    else:
        print("⚠️ Изображение не скачано")
else:
    print("⚠️ Нет URL изображения")

print("\n" + "=" * 60)
print("🏁 ГОТОВО! Изображение сохранено в Baserow (без внешней ссылки)")
print("=" * 60)
