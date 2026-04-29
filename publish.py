import requests
import os
import json

print("=" * 60)
print("🚀 PUBLISHER STARTED (ДИАГНОСТИКА)")
print("=" * 60)

TOKEN = os.environ.get("BASEROW_TOKEN")
TABLE_ID = os.environ.get("BASEROW_TABLE_ID")

print(f"BASEROW_TOKEN: {'✅ ЕСТЬ' if TOKEN else '❌ НЕТ'}")
print(f"BASEROW_TABLE_ID: {'✅ ЕСТЬ' if TABLE_ID else '❌ НЕТ'}")

if not TOKEN or not TABLE_ID:
    exit(1)

API_URL = f"https://api.baserow.io/api/database/rows/table/{TABLE_ID}/"
HEADERS = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json"
}

# 1. Получаем список строк
print("\n📡 1. ПОЛУЧАЮ СПИСОК СТРОК...")
params = {"user_field_names": "true", "size": 5}
response = requests.get(API_URL, headers=HEADERS, params=params)

print(f"Статус ответа: {response.status_code}")

if response.status_code != 200:
    print(f"Ошибка: {response.text}")
    exit(1)

rows = response.json().get("results", [])
print(f"Найдено строк: {len(rows)}")

# 2. Ищем первую строку с пустым Status
target_row = None
for row in rows:
    status = row.get("Status")
    print(f"\n--- Строка ID: {row.get('id')} ---")
    print(f"Start text: {row.get('Start text', '')[:60]}...")
    print(f"Status: '{status}' (тип: {type(status).__name__})")
    
    if status is None or status == "":
        target_row = row
        print("👉 ЭТА СТРОКА БУДЕТ ОБНОВЛЕНА")
        break

if not target_row:
    print("\n❌ Нет строк с пустым Status")
    exit(0)

# 3. Обновляем строку
print(f"\n📝 2. ОБНОВЛЯЮ СТРОКУ ID: {target_row['id']}")

update_data = {
    "Status": "выполнено"
}

print(f"Отправляю данные: {json.dumps(update_data, ensure_ascii=False)}")

update_url = f"{API_URL}{target_row['id']}/"
update_response = requests.patch(update_url, headers=HEADERS, json=update_data)

print(f"Статус обновления: {update_response.status_code}")

if update_response.status_code == 200:
    print("✅ УСПЕШНО ОБНОВЛЕНО!")
    print(f"Ответ от Baserow: {json.dumps(update_response.json(), ensure_ascii=False, indent=2)}")
else:
    print(f"❌ ОШИБКА: {update_response.text}")

# 4. Проверяем, что статус действительно изменился
print("\n🔍 3. ПРОВЕРЯЮ, ИЗМЕНИЛСЯ ЛИ СТАТУС...")
check_response = requests.get(API_URL, headers=HEADERS, params={"user_field_names": "true"})
check_rows = check_response.json().get("results", [])

for row in check_rows:
    if row['id'] == target_row['id']:
        print(f"Текущий Status в Baserow: '{row.get('Status')}'")
        break

print("\n" + "=" * 60)
print("🏁 FINISH")
print("=" * 60)
