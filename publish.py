import requests
import os

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
    
    for row in rows:
        status = row.get("Status")
        if status is None or status == "":
            print(f"✅ Найдена строка ID: {row.get('id')}")
            print(f"📝 Текст: {row.get('Start text', '')[:80]}...")
            return row
    
    print("✅ Нет строк для обработки")
    return None

def update_status(row_id, status):
    """Обновляет статус строки"""
    url = f"{API_URL}{row_id}/"
    response = requests.patch(url, headers=HEADERS, json={"Status": status})
    return response.status_code == 200

def main():
    # Находим строку
    row = get_empty_row()
    if not row:
        print("🏁 Завершаем работу")
        return
    
    # Обновляем статус на "выполнено"
    if update_status(row["id"], "выполнено"):
        print(f"✅ Статус строки {row['id']} обновлён на 'выполнено'")
    else:
        print(f"❌ Не удалось обновить статус")
    
    print("=" * 50)
    print("🏁 PUBLISHER FINISHED")
    print("=" * 50)

if __name__ == "__main__":
    main()
