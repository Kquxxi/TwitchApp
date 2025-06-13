import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
load_dotenv('config.env')

import os
import json
from jinja2 import Environment, FileSystemLoader

load_dotenv()

client_id = os.getenv("TWITCH_CLIENT_ID")
client_secret = os.getenv("TWITCH_CLIENT_SECRET")

def get_token():
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    res = requests.post(url, params=params)
    response_json = res.json()
    #print("DEBUG RESPONSE:", response_json)  
    return response_json['access_token']

# Pobierz ID użytkownika
def get_user_id(username, token):
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {token}'
    }
    url = f"https://api.twitch.tv/helix/users?login={username}"
    res = requests.get(url, headers=headers)
    data = res.json()
    return data['data'][0]['id'] if data['data'] else None

# Pobierz klipy użytkownika z ostatnich 24h
def get_clips(user_id, token):
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {token}'
    }
    # 1. Obiekt daty dokładnie 24h temu (UTC)
    one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
    # 2. Zamiana na ciąg w formacie YYYY-MM-DDTHH:MM:SSZ
    started_at  = one_day_ago.strftime("%Y-%m-%dT%H:%M:%SZ")

    url = (
        f"https://api.twitch.tv/helix/clips"
        f"?broadcaster_id={user_id}"
        f"&started_at={started_at}"
        f"&first=100"
    )

    res = requests.get(url, headers=headers).json()
    if 'data' not in res:
        print("Błąd pobierania klipów:", res)
        return []

    # Zwracamy tylko klipy z min. 30 wyświetleń
    return [c for c in res['data'] if c.get('view_count', 0) >= 30]


# Generuj raport HTML
def generate_report(clips):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')
    html_output = template.render(clips=clips)
    with open('raport.html', 'w', encoding='utf-8') as f:
        f.write(html_output)

def get_games_info(game_ids, token):
    headers = {'Client-ID': client_id, 'Authorization': f'Bearer {token}'}
    params  = [('id', gid) for gid in game_ids]
    res     = requests.get("https://api.twitch.tv/helix/games", headers=headers, params=params).json()
    return {g['id']: g['name'] for g in res.get('data', [])}


if __name__ == "__main__":
    token = get_token()

    with open('streamerzy.json', encoding='utf-8') as f:
      creators = [s['login'] for s in json.load(f)['streamerzy']]

    all_clips = []
    for creator in creators:
        user_id = get_user_id(creator, token)
        if user_id:
            clips = get_clips(user_id, token)
            for clip in clips:
              all_clips.append({
                  'broadcaster': clip.get('broadcaster_name', '—'),
                  'title':   clip.get('title', '—'),
                  'url':     clip['url'],
                  'views':   clip['view_count'],
                  'game_id': clip.get('game_id', ''),
                  'created_at':  clip.get('created_at')
                })

# 1) zbierz unikalne ID gier
game_ids = list({c['game_id'] for c in all_clips if c['game_id']})
# 2) pobierz mapę id → nazwa
game_map = get_games_info(game_ids, token)
# 3) dodaj kategorię do każdego klipu
for c in all_clips:
    c['category'] = game_map.get(c['game_id'], '—')

now = datetime.now(timezone.utc)
for c in all_clips:
    # parsujemy ISO8601: usuwamy Z i dodajemy +00:00, żeby fromisoformat przyjął
    created = datetime.fromisoformat(c['created_at'].replace('Z', '+00:00'))
    delta   = now - created

    if delta.days >= 1:
        rel = f"{delta.days}d ago"
    elif delta.seconds >= 3600:
        rel = f"{delta.seconds // 3600}h ago"
    elif delta.seconds >= 60:
        rel = f"{delta.seconds // 60}m ago"
    else:
        rel = f"{delta.seconds}s ago"

    c['relative_time'] = rel

# teraz sortuj i generuj raport
sorted_clips = sorted(all_clips, key=lambda x: x['views'], reverse=True)
generate_report(sorted_clips)


print("Raport został wygenerowany do pliku raport.html!")
