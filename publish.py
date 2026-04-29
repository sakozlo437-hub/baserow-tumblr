import requests
import os
import re

print("=" * 50)
print("🚀 PUBLISHER STARTED")
print("=" * 50)

# Получаем секреты
TOKEN = os.environ.get("BASEROW_TOKEN")
TABLE_ID = os.environ.get("BASEROW_TABLE_ID")

print(f"📌 BASEROW_TOKEN: {'✅ НАЙДЕН' if TOKEN else '❌ ОТСУТСТВУЕТ'}")
print(f"📌 BASEROW_TABLE_ID: {'✅ НАЙДЕН' if TABLE_ID else '❌ ОТСУТСТВУЕТ'}")

if not TOKEN or not TABLE_ID:
    print("❌ Ошибка: секреты не настроены!")
    exit(1)

# API настройки
API_URL = f"https://api.baserow.io/api/database/rows/table/{TABLE_ID}/"
HEADERS = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json"
}

def get_empty_row():
    """Находит первую строку с пустым Status"""
    print("🔍 Ищу строку с пустым Status...")
    
    params = {
        "user_field_names": "true",
        "size": 10
    }
    
    response = requests.get(API_URL, headers=HEADERS, params=params)
    
    if response.status_code != 200:
        print(f"❌ Ошибка API: {response.status_code}")
        print(f"Ответ: {response.text[:200]}")
        return None
    
    rows = response.json().get("results", [])
    print(f"📊 Найдено строк в таблице: {len(rows)}")
    
    for row in rows:
        status = row.get("Status")
        print(f"  - Строка ID {row.get('id')}: Status = '{status}'")
        if status is None or status == "":
            print(f"✅ Найдена пустая строка ID: {row.get('id')}")
            return row
    
    print("✅ Нет строк для обработки")
    return None

def update_row(row_id, data):
    """Обновляет данные строки"""
    url = f"{API_URL}{row_id}/"
    response = requests.patch(url, headers=HEADERS, json=data)
    return response

def call_ai(start_text):
    """Отправляет запрос в Cloudfleur AI (пока заглушка)"""
    print("🤖 Генерирую SEO-контент...")
    
    # Временная заглушка (без реального API)
    # Потом заменишь на реальный запрос к Cloudfleur
    
    return {
        "title": f"🔥 {start_text[:50]}",
        "body_text": f"Feeling like a little piece of summer! ☀️\n\n{start_text[:150]}...\n\nPure beach happiness! ✨\n\nPerfect fit, nothing digs in, nothing slips — just pure happiness!",
        "slug": re.sub(r'[^a-z0-9-]', '-', start_text[:50].lower().replace(' ', '-')),
        "tags": "bikini, summer, beach, swimwear, fashion, vacation"
    }

def main():
    # Находим строку для обработки
    row = get_empty_row()
    if not row:
        print("🏁 Завершаем работу")
        return
    
    start_text = row.get("Start text", "")
    print(f"📝 Текст для обработки: {start_text[:80]}...")
    
    # 1. Получаем данные от ИИ
    ai_data = call_ai(start_text)
    print(f"✅ Сгенерирован Title: {ai_data['title'][:50]}...")
    
    # 2. Обновляем таблицу
    print("📝 Обновляю Baserow...")
    
    update_data = {
        "Title": ai_data['title'],
        "Body text": ai_data['body_text'],
        "Slug": ai_data['slug'],
        "Tags": ai_data['tags'],
        "Status": "выполнено"  # Простой текст, не Single select
    }
    
    result = update_row(row["id"], update_data)
    
    if result.status_code == 200:
        print(f"✅ Строка {row['id']} успешно обновлена!")
        print(f"   - Title: {ai_data['title'][:40]}...")
        print(f"   - Status: выполнено")
    else:
        print(f"❌ Ошибка обновления: {result.status_code}")
        print(f"   Ответ: {result.text[:200]}")
    
    print("=" * 50)
    print("🏁 PUBLISHER FINISHED")
    print("=" * 50)

if __name__ == "__main__":
    main()
