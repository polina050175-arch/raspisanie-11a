import os
import hashlib
import requests
import csv
from io import StringIO

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SHEET_URL = "https://docs.google.com/spreadsheets/d/1RD6NdK7Hvu_5exUVF15-Jz1tfduV1jQygOkmmbx1O2Q/export?format=csv"
HASH_FILE = "last_hash.txt"

def get_schedule_11a():
    response = requests.get(SHEET_URL, timeout=30)
    response.raise_for_status()
    response.encoding = 'utf-8'
    
    reader = csv.reader(StringIO(response.text))
    rows = list(reader)
    
    headers = rows[2]
    col = None
    for i, h in enumerate(headers):
        if h.strip() == "11А":
            col = i
            break
    
    if col is None:
        return "❌ Не нашёл столбец 11А", ""
    
    message = "📅 *Расписание 11А*\n_Обновлено_\n\n"
    current_day = ""
    
    for row in rows[3:]:
        if len(row) <= col:
            continue
        day = row[0].strip() if row[0] else ""
        lesson = row[1].strip() if len(row) > 1 else ""
        time = row[2].strip() if len(row) > 2 else ""
        subject = row[col].strip() if row[col] else ""
        
        if day:
            current_day = day
        
        if subject:
            if day:
                message += f"\n*{current_day}*\n"
            message += f"{lesson}. {time} — {subject}\n"
    
    content_for_hash = "\n".join([row[col] if len(row) > col else "" for row in rows[3:]])
    return message, content_for_hash

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }, timeout=30)

def main():
    message, content = get_schedule_11a()
    current_hash = hashlib.md5(content.encode()).hexdigest()
    
    old_hash = ""
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            old_hash = f.read().strip()
    
    if current_hash != old_hash:
        send_telegram(message)
        with open(HASH_FILE, "w") as f:
            f.write(current_hash)
        print("Расписание изменилось — отправил")
    else:
        print("Изменений нет")

if __name__ == "__main__":
    main()
