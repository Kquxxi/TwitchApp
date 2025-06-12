import requests
from dotenv import load_dotenv
load_dotenv('config.env')

import os
import json
from datetime import datetime, timedelta
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
    print("DEBUG RESPONSE:", response_json)  
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
    started_at = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
    url = f"https://api.twitch.tv/helix/clips?broadcaster_id={user_id}&started_at={started_at}"
    res = requests.get(url, headers=headers)
    return res.json()['data']

# Generuj raport HTML
def generate_report(clips):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')
    html_output = template.render(clips=clips)
    with open('raport.html', 'w', encoding='utf-8') as f:
        f.write(html_output)

if __name__ == "__main__":
    token = get_token()

    with open('tworcy.json') as f:
        creators = json.load(f)['tworcy']

    all_clips = []
    for creator in creators:
        user_id = get_user_id(creator, token)
        if user_id:
            clips = get_clips(user_id, token)
            for clip in clips:
                all_clips.append({
                    'creator': creator,
                    'url': clip['url'],
                    'views': clip['view_count']
                })

    sorted_clips = sorted(all_clips, key=lambda x: x['views'], reverse=True)

    generate_report(sorted_clips)

    print("Raport został wygenerowany do pliku raport.html!")
