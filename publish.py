import requests
import os
import json

print("=" * 60)
print("🚀 FINAL FIXED VERSION")
print("=" * 60)

TOKEN = os.environ.get("BASEROW_TOKEN")
TABLE_ID = os.environ.get("BASEROW_TABLE_ID")

print(f"TOKEN: {'✅' if TOKEN else '❌'}")
print(f"TABLE_ID: {'✅' if TABLE_ID else '❌'}")

if not TOKEN or not TABLE_ID:
    exit(1)

API_URL = f"https://api.baserow.io/api/database/rows/table/{TABLE_ID}/"
HEADERS = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json"
}

# ID поля Status (ты посмотрела в Baserow)
STATUS_FIELD_ID = 8259562

print(f"\n📌 Status field ID: {STATUS_FIELD_ID}")

# 1. Получаем строки
print("\n📡 1. Getting rows...")
params = {"size": 10}
resp = requests.get(API_URL, headers=HEADERS, params=params)

if resp.status_code != 200:
    print(f"❌ Error: {resp.text}")
    exit(1)

rows = resp.json().get("results", [])
print(f"Total rows: {len(rows)}")

# 2. Ищем пустую строку
target = None
for row in rows:
    status_value = row.get(f"field_{STATUS_FIELD_ID}")
    print(f"  Row {row['id']}: Status = '{status_value}'")
    
    if status_value is None or status_value == "":
        target = row
        print(f"  👉 THIS ROW WILL BE UPDATED")
        break

if not target:
    print("\n❌ No empty rows found")
    exit(0)

# 3. Обновляем статус
print(f"\n📝 2. Updating row {target['id']}...")

update_data = {f"field_{STATUS_FIELD_ID}": "выполнено"}
print(f"Payload: {json.dumps(update_data, ensure_ascii=False)}")

patch_resp = requests.patch(
    f"{API_URL}{target['id']}/",
    headers=HEADERS,
    json=update_data
)

print(f"Response status: {patch_resp.status_code}")

if patch_resp.status_code == 200:
    print("✅ UPDATE SUCCESSFUL!")
    print(f"Response: {json.dumps(patch_resp.json(), ensure_ascii=False, indent=2)}")
else:
    print(f"❌ UPDATE FAILED: {patch_resp.text}")
    exit(1)

# 4. Проверяем
print("\n🔍 3. Verifying...")
check_resp = requests.get(API_URL, headers=HEADERS, params={"size": 1})
check_row = check_resp.json()["results"][0]
current_status = check_row.get(f"field_{STATUS_FIELD_ID}")
print(f"Current Status in Baserow: '{current_status}'")

if current_status == "выполнено":
    print("\n🎉 SUCCESS! Status updated correctly!")
else:
    print(f"\n⚠️ Status is still: '{current_status}'")

print("\n" + "=" * 60)
print("🏁 DONE")
