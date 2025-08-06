import os, json, sys
from datetime import datetime, timedelta, timezone
from kickapi import KickAPI

sys.stdout.reconfigure(encoding='utf-8')
api = KickAPI()
base = os.path.dirname(__file__)

with open(os.path.join(base, 'kick_database.json'), encoding='utf-8') as f:
    streamers = json.load(f)['database']

now = datetime.now(timezone.utc)
day_ago = now - timedelta(days=1)

# --- Wczytaj stare klipy (jeśli plik istnieje)
cache_path = os.path.join(base, 'kick_clips_cache.json')
if os.path.exists(cache_path):
    with open(cache_path, encoding='utf-8') as f:
        old_clips = json.load(f)
else:
    old_clips = []

# Zamien na dict po url (albo ID jak masz)
clip_dict = {c['url']: c for c in old_clips}

def get_clips_kick(slug):
    try:
        clips = api.channel(slug).clips
        return [
            {
                'broadcaster': s['display_name'],
                'title': c.title,
                'url': f"https://kick.com/{slug}/clips/{c.id}",
                'views': c.views,
                'created_at': c.created_at,
            }
            for c in clips
            if datetime.fromisoformat(c.created_at.replace('Z','+00:00')) > day_ago
        ]
    except Exception as e:
        print(f"[ERROR] {slug}: {e}")
        return []

# --- Update'ujemy stare klipy
for s in streamers:
    for c in get_clips_kick(s['slug']):
        if c['url'] in clip_dict:
            # Update liczby wyświetleń i tytułu jeśli się zmienił
            clip_dict[c['url']]['views'] = c['views']
            clip_dict[c['url']]['title'] = c['title']
        else:
            # Dodaj nowy klip
            clip_dict[c['url']] = c

# Filtrujemy klipy tylko z ostatnich 24h
final_clips = [
    c for c in clip_dict.values()
    if datetime.fromisoformat(c['created_at'].replace('Z','+00:00')) > day_ago
]

with open(cache_path, 'w', encoding='utf-8') as f:
    json.dump(final_clips, f, ensure_ascii=False, indent=2)

print(f"[OK] Zapisano {len(final_clips)} klipów w kick_clips_cache.json")
