import os, json, requests, time, concurrent.futures
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
load_dotenv('config.env')
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
sys.stdout.reconfigure(encoding='utf-8')

CLIENT_ID     = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

session = requests.Session()
retries = Retry(total=3,
                backoff_factor=1,        # 1s, 2s, 4s przerwy
                status_forcelist=[429, 500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

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
    if 'access_token' not in response_json:
        # wyświetlamy całą odpowiedź do debugowania
        print("Błąd podczas pobierania tokena:", response_json)
        exit(1)  
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

    time.sleep(0.1)
    res = session.get(url, headers=headers).json()
    if 'data' not in res:
        print("Błąd pobierania klipów:", res)
        return []

    # Zwracamy tylko klipy z min. 30 wyświetleń
    return [c for c in res['data'] if c.get('view_count', 0) >= 30]


# Generuj raport HTML
def generate_raport(clips,stats):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')
    html_output = template.render(clips=clips, stats=stats)
    with open('raport.html', 'w', encoding='utf-8') as f:
        f.write(html_output)

def get_games_info(game_ids, token):
    headers = {'Client-ID': client_id, 'Authorization': f'Bearer {token}'}
    params  = [('id', gid) for gid in game_ids]
    res     = requests.get("https://api.twitch.tv/helix/games", headers=headers, params=params).json()
    return {g['id']: g['name'] for g in res.get('data', [])}


if __name__ == "__main__":
    token = get_token()

    with open('database.json', encoding='utf-8') as f:
        streamers = json.load(f)['database']
    #print(f"[DEBUG] Załadowano {len(streamers)} streamerów")

max_workers = min(5, len(streamers))  # liczba wątków równoległych (dostosuj do swojego łącza/API limits)
all_clips = []

with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    future_to_streamer = {
        executor.submit(get_clips, s['id'], token): s
        for s in streamers
    }

    for future in as_completed(future_to_streamer):
        s = future_to_streamer[future]
        try:
            clips = future.result()
        except Exception as e:
            print(f"[ERROR] Błąd dla {s['display_name']}: {e}")
            continue

        #print(f"[DEBUG] -> {len(clips)} klipow dla {s['display_name']}")

        for clip in clips:
            all_clips.append({
                'broadcaster':  s['display_name'],
                'title':        clip.get('title', '—'),
                'url':          clip['url'],
                'views':        clip['view_count'],
                'game_id':      clip.get('game_id', ''),
                'created_at':   clip.get('created_at')
            })

#print(f"[DEBUG] Razem wyfiltrowanych klipow: {len(all_clips)}")

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

# teraz sortuj, oblicz statystyki i generuj raport
sorted_clips = sorted(all_clips, key=lambda x: x['views'], reverse=True)

# Obliczamy statystyki (total_clips, top3 kategorie, top3 streamerzy, avg/median)
total_clips = len(sorted_clips)
from collections import Counter
cat_counts       = Counter(c['category'] for c in sorted_clips)
top3_categories  = cat_counts.most_common(3)
broad_counts     = Counter(c['broadcaster'] for c in sorted_clips)
top3_streamers   = broad_counts.most_common(3)
import statistics
views            = [c['views'] for c in sorted_clips]

stats = {
    'total_clips':    total_clips,
    'top_categories': top3_categories,
    'top_streamers':  top3_streamers,
    
}

generate_raport(sorted_clips, stats)

with open('raport_data.json','w',encoding='utf-8') as f:
    json.dump({'clips': sorted_clips, 'stats': stats}, f, ensure_ascii=False, indent=2)

print("Raport został wygenerowany do pliku raport.html!")
