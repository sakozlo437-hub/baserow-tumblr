import requests
import os
import json
import re

print("=" * 60)
print("🚀 AI CONTENT GENERATOR (Gemma 4)")
print("=" * 60)

# 🔐 Получаем ключи из секретов
TOKEN = os.environ.get("BASEROW_TOKEN")
TABLE_ID = os.environ.get("BASEROW_TABLE_ID")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")  # ← из секрета

print(f"BASEROW_TOKEN: {'✅' if TOKEN else '❌'}")
print(f"BASEROW_TABLE_ID: {'✅' if TABLE_ID else '❌'}")
print(f"OPENROUTER_API_KEY: {'✅' if OPENROUTER_API_KEY else '❌'}")

if not TOKEN or not TABLE_ID or not OPENROUTER_API_KEY:
    print("❌ Ошибка: не все секреты настроены")
    exit(1)

API_URL = f"https://api.baserow.io/api/database/rows/table/{TABLE_ID}/"
HEADERS = {"Authorization": f"Token {TOKEN}", "Content-Type": "application/json"}

FIELD_IDS = {
    "Start text": 8259553,
    "Title": 8259555,
    "Body text": 8259556,
    "Slug": 8259560,
    "Tags": 8259561,
    "Status": 8259562
}

def call_ai(start_text):
    print(f"\n🤖 Gemma 4: {start_text[:80]}...")
    
    prompt = f"""Ты SEO-специалист. Создай контент для: "{start_text}"
Ответь ТОЛЬКО JSON: {{"title":"...", "body_text":"...", "slug":"...", "tags":"..."}}
title: до 60 символов с эмодзи
body_text: 2-3 эмоциональных предложения как 'кусочек лета'
slug: только латиница и дефисы
tags: 5 тегов через запятую"""

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
        
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise Exception("JSON не найден")
        else:
            raise Exception(f"HTTP {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Ошибка Gemma 4: {e}")
    
    # Заглушка
    return {
        "title": f"✨ {start_text[:50]}",
        "body_text": f"Feeling like a little piece of summer! ☀️\n\n{start_text[:100]}...\n\nPure beach happiness! ✨",
        "slug": re.sub(r'[^a-z0-9-]', '-', start_text[:50].lower().replace(' ', '-')),
        "tags": "summer, beach, fashion, swimwear, vacation"
    }

# Поиск пустой строки
print("\n📡 Поиск строки с пустым Status...")
resp = requests.get(API_URL, headers=HEADERS, params={"size": 10})

if resp.status_code != 200:
    print(f"❌ Ошибка API: {resp.text}")
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
    print("\n❌ Нет строк для обработки")
    exit(0)

start_text = target.get(f"field_{FIELD_IDS['Start text']}", "")
print(f"\n📝 Start text: {start_text[:100]}...")

# Генерация контента
ai_data = call_ai(start_text)

print(f"\n📊 Результаты от ИИ:")
print(f"   Title: {ai_data.get('title', '')[:60]}")
print(f"   Body: {ai_data.get('body_text', '')[:80]}...")
print(f"   Slug: {ai_data.get('slug', '')}")
print(f"   Tags: {ai_data.get('tags', '')}")

# Обновление таблицы
print(f"\n📝 Обновление строки {target['id']}...")

update_data = {
    f"field_{FIELD_IDS['Title']}": ai_data.get("title", ""),
    f"field_{FIELD_IDS['Body text']}": ai_data.get("body_text", ""),
    f"field_{FIELD_IDS['Slug']}": ai_data.get("slug", ""),
    f"field_{FIELD_IDS['Tags']}": ai_data.get("tags", ""),
    f"field_{FIELD_IDS['Status']}": "выполнено"
}

patch_resp = requests.patch(
    f"{API_URL}{target['id']}/",
    headers=HEADERS,
    json=update_data
)

if patch_resp.status_code == 200:
    print("✅ UPDATE SUCCESSFUL!")
    
    # Проверка
    check_row = patch_resp.json()
    new_status = check_row.get(f"field_{FIELD_IDS['Status']}")
    print(f"✅ Новый статус: '{new_status}'")
else:
    print(f"❌ Ошибка: {patch_resp.text}")
    exit(1)

print("\n" + "=" * 60)
print("🏁 DONE! Проверь Baserow")
print("=" * 60)
