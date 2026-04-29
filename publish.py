import requests
import os
import json

print("=" * 60)
print("🚀 DIAGNOSTIC MODE")
print("=" * 60)

TOKEN = os.environ.get("BASEROW_TOKEN")
TABLE_ID = os.environ.get("BASEROW_TABLE_ID")

print(f"TOKEN: {'✅' if TOKEN else '❌'}")
print(f"TABLE_ID: {'✅' if TABLE_ID else '❌'}")

if not TOKEN or not TABLE_ID:
    exit(1)

API_URL = f"https://api.baserow.io/api/database/rows/table/{TABLE_ID}/"
HEADERS = {"Authorization": f"Token {TOKEN}", "Content-Type": "application/json"}

# 1. ПОЛУЧАЕМ ВСЕ СТРОКИ
print("\n📡 1. GET /rows/")
params = {"user_field_names": "true", "size": 5}
resp = requests.get(API_URL, headers=HEADERS, params=params)
print(f"Status: {resp.status_code}")

if resp.status_code != 200:
    print(f"Error: {resp.text}")
    exit(1)

rows = resp.json().get("results", [])
print(f"Total rows: {len(rows)}")

# 2. ИЩЕМ ПУСТУЮ СТРОКУ
target = None
for row in rows:
    status = row.get("Status")
    print(f"\n--- Row {row.get('id')} ---")
    print(f"Status: '{status}' (type: {type(status).__name__})")
    print(f"Start text: {row.get('Start text', '')[:50]}")
    
    if status is None or status == "":
        target = row
        print("👉 THIS ROW WILL BE UPDATED")
        break

if not target:
    print("\n❌ No empty rows")
    exit(0)

# 3. ОБНОВЛЯЕМ СТРОКУ
print(f"\n📝 2. PATCH /rows/{target['id']}/")
update_data = {"Status": "выполнено"}
print(f"Payload: {json.dumps(update_data, ensure_ascii=False)}")

patch_resp = requests.patch(
    f"{API_URL}{target['id']}/",
    headers=HEADERS,
    json=update_data
)

print(f"Status: {patch_resp.status_code}")

if patch_resp.status_code == 200:
    print("✅ UPDATE SUCCESSFUL")
    print(f"Response: {json.dumps(patch_resp.json(), ensure_ascii=False, indent=2)}")
else:
    print(f"❌ UPDATE FAILED: {patch_resp.text}")

# 4. ПРОВЕРЯЕМ
print("\n🔍 3. VERIFYING...")
check = requests.get(API_URL, headers=HEADERS, params={"user_field_names": "true"})
for row in check.json().get("results", []):
    if row["id"] == target["id"]:
        print(f"Current Status in Baserow: '{row.get('Status')}'")
        break

print("\n" + "=" * 60)
print("🏁 DONE")
