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

# --- 1. Wczytaj istniejące klipy z pliku (jeśli jest) ---
cache_path = os.path.join(base, 'kick_clips_cache.json')
if os.path.exists(cache_path):
    with open(cache_path, encoding='utf-8') as f:
        clips_cache = json.load(f)
else:
    clips_cache = []

# Indeks istniejących po URL (lub możesz użyć id klipa jeśli masz w strukturze)
clip_urls = set(c['url'] for c in clips_cache)

def get_clips_kick(slug, display_name):
    try:
        clips = api.channel(slug).clips
        return [
            {
                'broadcaster': display_name,
                'title': c.title,
                'url': f"https://kick.com/{slug}/clips/{c.id}",
                'views': c.views,
                'created_at': c.created_at,  # ISO string!
            }
            for c in clips
            if datetime.fromisoformat(c.created_at.replace('Z','+00:00')) > day_ago
        ]
    except Exception as e:
        print(f"[ERROR] {slug}: {e}")
        return []

# --- 2. Dodajemy nowe klipy jeśli ich nie było ---
new_clips_count = 0
for s in streamers:
    new_clips = get_clips_kick(s['slug'], s['display_name'])
    for clip in new_clips:
        if clip['url'] not in clip_urls:
            clips_cache.append(clip)
            clip_urls.add(clip['url'])
            new_clips_count += 1

# --- 3. Zapisujemy plik cache (dodane stare+nowe klipy) ---
with open(cache_path, 'w', encoding='utf-8') as f:
    json.dump(clips_cache, f, ensure_ascii=False, indent=2)

print(f"[OK] Dodano {new_clips_count} nowych klipów. Łącznie w bazie: {len(clips_cache)}.")
