# todo
# - make it so it will print to docker logs


import requests
import json
import os
import time
from dotenv import load_dotenv
from datetime import datetime
from collections import Counter

# Load environment variables
load_dotenv()

# Discord webhook URL
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK')

# API URL
API_URL = 'https://www.ple.com.au/api/fetchKnowledgebase/5'

# Determine the base directory
BASE_DIR = os.environ.get('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))

# File to store vacancy history
VACANCY_HISTORY_FILE = os.path.join(BASE_DIR, 'data', 'vacancy_history.json')

# Check interval in seconds (30 minutes)
CHECK_INTERVAL = 1800

def get_vacancies():
    headers = {
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
        'content-type': 'application/json',
        'Referer': 'https://www.ple.com.au/',
        'pleauthkey': 'null',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0',
        'sec-ch-ua-platform': '"Windows"'
    }

    response = requests.get(API_URL, headers=headers)
    data = response.json()
    
    return {item['QuestionHtmlText']: item['LastUpdatedDateTime'] for item in data['data']['KnowledgebaseItems']}

def load_vacancy_history():
    os.makedirs(os.path.dirname(VACANCY_HISTORY_FILE), exist_ok=True)
    if os.path.exists(VACANCY_HISTORY_FILE):
        with open(VACANCY_HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_vacancy_history(history):
    with open(VACANCY_HISTORY_FILE, 'w') as f:
        json.dump(history, f)

def send_discord_message(message):
    payload = {
        'content': message
    }
    requests.post(DISCORD_WEBHOOK, json=payload)

def format_date(date_string):
    date_object = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%f")
    return date_object.strftime("%d %B %Y")  # e.g., "29 May 2024"

def check_vacancies():
    current_vacancies = get_vacancies()
    vacancy_history = load_vacancy_history()
    current_time = datetime.now().isoformat()

    current_vacancy_count = Counter(current_vacancies.keys())
    previous_vacancy_count = Counter(vacancy_history.keys())

    new_vacancies = []
    removed_vacancies = []

    for vacancy, last_updated in current_vacancies.items():
        previous_count = previous_vacancy_count.get(vacancy, 0)
        current_count = current_vacancy_count[vacancy]
        
        if current_count > previous_count:
            new_vacancies.extend([(vacancy, last_updated)] * (current_count - previous_count))
        
        vacancy_history[vacancy] = {
            'count': current_count,
            'last_seen': current_time,
            'last_updated': last_updated
        }

    for vacancy, count in previous_vacancy_count.items():
        current_count = current_vacancy_count.get(vacancy, 0)
        if current_count < count:
            removed_vacancies.extend([vacancy] * (count - current_count))
        
        if current_count == 0:
            vacancy_history.pop(vacancy, None)

    if new_vacancies:
        message = "New vacancies:\n" + "\n".join(f"• {vacancy} ({format_date(last_updated)})" for vacancy, last_updated in new_vacancies)
        send_discord_message(message)

    if removed_vacancies:
        message = "Removed vacancies:\n" + "\n".join(f"• {vacancy}" for vacancy in removed_vacancies)
        send_discord_message(message)

    if new_vacancies or removed_vacancies:
        save_vacancy_history(vacancy_history)
        print(f"Updates sent at {datetime.now()}")
    else:
        print(f"No changes detected at {datetime.now()}")

def main():
    print("Vacancy checker started. Checking every 30 minutes.")
    while True:
        try:
            check_vacancies()
        except Exception as e:
            print(f"An error occurred: {e}")
            send_discord_message(f"An error occurred in the vacancy checker: {e}")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
