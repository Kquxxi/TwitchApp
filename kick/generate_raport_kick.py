import os, json, sys
from datetime import datetime, timedelta, timezone
from collections import Counter
from kickapi import KickAPI
from jinja2 import Environment, FileSystemLoader

sys.stdout.reconfigure(encoding='utf-8')
api = KickAPI()

base = os.path.dirname(__file__)
# 1) Wczytaj streamerów
with open(os.path.join(base,'kick_database.json'), encoding='utf-8') as f:
    streamers = json.load(f)['database']

now = datetime.now(timezone.utc)
all_clips = []

def get_clips_kick(slug):
    clips = api.channel(slug).clips
    day_ago = now - timedelta(days=1)
    recent = [
        c for c in clips
        if datetime.fromisoformat(c.created_at.replace('Z','+00:00')) > day_ago
    ]
    recent.sort(key=lambda c: c.views, reverse=True)
    return recent

# 2) Zbierz dane
for s in streamers:
    try:
        clips = get_clips_kick(s['slug'])
    except Exception as e:
        print(f"[ERROR] {s['slug']}: {e}")
        continue

    for c in clips:
        created = datetime.fromisoformat(c.created_at.replace('Z','+00:00'))
        delta   = now - created
        if delta.days > 0:
            rel = f"{delta.days}d ago"
        elif delta.seconds >= 3600:
            rel = f"{delta.seconds//3600}h ago"
        elif delta.seconds >= 60:
            rel = f"{delta.seconds//60}m ago"
        else:
            rel = f"{delta.seconds}s ago"

        all_clips.append({
            'broadcaster':   s['display_name'],
            'title':         c.title,
            'url':           f"https://kick.com/{s['slug']}/clips/{c.id}",
            'views':         c.views,
            'relative_time': rel
        })
    all_clips = [c for c in all_clips if c['views'] > 20]
    all_clips.sort(key=lambda c: c['views'], reverse=True)

# 3) Oblicz statystyki top3
b_counts       = Counter(c['broadcaster'] for c in all_clips)
stats = {
    'total_clips':    len(all_clips),
    'top_streamers':  b_counts.most_common(3)
}

# 4) Renderuj JSON i pełny HTML
with open(os.path.join(base,'raport_kick_data.json'), 'w', encoding='utf-8') as f:
    json.dump({'clips': all_clips, 'stats': stats},
              f, ensure_ascii=False, indent=2)

env = Environment(loader=FileSystemLoader(base))
tpl = env.get_template('template_kick.html')   # pełny raport jeśli go używasz
html = tpl.render(clips=all_clips, stats=stats)
with open(os.path.join(base,'raport_kick.html'), 'w', encoding='utf-8') as f:
    f.write(html)

print("Kick‑raport wygenerowany: kick/raport_kick.html")
