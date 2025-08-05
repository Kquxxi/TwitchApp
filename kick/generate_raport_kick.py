import os, json, sys
from datetime import datetime, timedelta, timezone
from collections import Counter
from jinja2 import Environment, FileSystemLoader

sys.stdout.reconfigure(encoding='utf-8')
base = os.path.dirname(__file__)

with open(os.path.join(base, 'kick_clips_cache.json'), encoding='utf-8') as f:
    all_clips = json.load(f)

now = datetime.now(timezone.utc)
day_ago = now - timedelta(days=1)

# Filtruj i sortuj jak dotąd:
filtered = [
    {
        'broadcaster': c['broadcaster'],
        'title': c['title'],
        'url': c['url'],
        'views': c['views'],
        'relative_time': (
            lambda created:
                f"{(now-delta).days}d ago" if (delta := now - datetime.fromisoformat(created.replace('Z','+00:00'))).days > 0
            else f"{delta.seconds//3600}h ago" if delta.seconds >= 3600
            else f"{delta.seconds//60}m ago" if delta.seconds >= 60
            else f"{delta.seconds}s ago"
        )(c['created_at'])
    }
    for c in all_clips
    if datetime.fromisoformat(c['created_at'].replace('Z','+00:00')) > day_ago and c['views'] > 20
]

filtered.sort(key=lambda c: c['views'], reverse=True)

# Statystyki
b_counts = Counter(c['broadcaster'] for c in filtered)
stats = {
    'total_clips': len(filtered),
    'top_streamers': b_counts.most_common(3)
}

with open(os.path.join(base,'raport_kick_data.json'), 'w', encoding='utf-8') as f:
    json.dump({'clips': filtered, 'stats': stats}, f, ensure_ascii=False, indent=2)

# Render HTML (jak dotąd)
env = Environment(loader=FileSystemLoader(base))
tpl = env.get_template('template_kick.html')
html = tpl.render(clips=filtered, stats=stats)
with open(os.path.join(base, 'raport_kick.html'), 'w', encoding='utf-8') as f:
    f.write(html)

print("Kick‑raport wygenerowany: kick/raport_kick.html")
