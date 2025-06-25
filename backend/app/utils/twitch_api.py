import os
import requests
from datetime import datetime, timedelta, timezone

CLIENT_ID     = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

def get_token() -> str:
    """Zwróć access_token do Helix API."""
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    r = requests.post(url, params=params)
    r.raise_for_status()
    return r.json()["access_token"]

def fetch_streamers(min_followers: int = 1000) -> list[dict]:
    """Pobierz listę polskich streamerów z ≥ min_followers followers."""
    token = get_token()
    headers = {"Client-ID": CLIENT_ID, "Authorization": f"Bearer {token}"}
    # Tu implementacja: /helix/users/follows lub /streams?language=pl + dodatkowe filtrowanie
    # Zwraca listę dictów: {"id":..., "login":..., "display_name":..., "follower_count":...}
    ...

def fetch_clips(streamer_ids: list[str], min_views: int = 30) -> list[dict]:
    """Pobierz klipy ostatnich 24h dla listy streamerów, filtrowane po widzach."""
    token = get_token()
    headers = {"Client-ID": CLIENT_ID, "Authorization": f"Bearer {token}"}
    since = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    clips = []
    for uid in streamer_ids:
        url = (
            "https://api.twitch.tv/helix/clips"
            f"?broadcaster_id={uid}&started_at={since}&first=100"
        )
        data = requests.get(url, headers=headers).json().get("data", [])
        for c in data:
            if c.get("view_count", 0) >= min_views:
                clips.append({
                    "broadcaster": c["broadcaster_name"],
                    "title":       c["title"],
                    "url":         c["url"],
                    "views":       c["view_count"],
                    "created_at":  c["created_at"],
                    "game_id":     c.get("game_id", "")
                })
    return clips
