import requests
import os
import json
from dotenv import load_dotenv

load_dotenv('config.env')
CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

def get_token():
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    res = requests.post(url, params=params)
    return res.json()['access_token']

def fetch_polish_streamers(token, max_pages=5):
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}'
    }
    streamers = []
    url = "https://api.twitch.tv/helix/streams"
    params = {'language': 'pl', 'first': 100}
    for _ in range(max_pages):
        res = requests.get(url, headers=headers, params=params).json()
        data = res.get('data', [])
        for s in data:
            streamers.append({
                'id': s['user_id'],
                'login': s['user_login'],
                'display_name': s['user_name']
            })
        # paginacja
        cursor = res.get('pagination', {}).get('cursor')
        if not cursor:
            break
        params['after'] = cursor
    return streamers

def load_existing():
    with open('streamerzy.json', encoding='utf-8') as f:
        return json.load(f)

def save(streamers_data):
    with open('streamerzy.json', 'w', encoding='utf-8') as f:
        json.dump({'streamerzy': streamers_data}, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    token = get_token()
    new_list = fetch_polish_streamers(token)
    db = load_existing()['streamerzy']

    # Dodaj tylko unikalnych
    existing_ids = {s['id'] for s in db}
    added = 0
    for s in new_list:
        if s['id'] not in existing_ids:
            db.append(s)
            added += 1

    save(db)
    print(f"Dodano {added} nowych streamerów. Łącznie w bazie: {len(db)}.")
