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
clips_cache = []

def get_clips_kick(slug):
    try:
        clips = api.channel(slug).clips
        return [
            {
                'broadcaster': s['display_name'],
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

for s in streamers:
    clips_cache.extend(get_clips_kick(s['slug']))

with open(os.path.join(base, 'kick_clips_cache.json'), 'w', encoding='utf-8') as f:
    json.dump(clips_cache, f, ensure_ascii=False, indent=2)

print(f"[OK] Zapisano {len(clips_cache)} klipów w kick_clips_cache.json")
