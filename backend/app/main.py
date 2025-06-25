from fastapi import FastAPI, Depends, Query
from fastapi.responses import JSONResponse
from collections import Counter
from sqlalchemy.orm import Session
from app import schemas, models
from app.database import engine, SessionLocal, Base
from app.utils import twitch_api  # ← importujemy helpery

# Tworzymy tabele, jeśli nie istnieją
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Twitch Clips Backend")

# Dependency: sesja DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/streamers/", response_model=schemas.Streamer)
def create_streamer(s: schemas.StreamerCreate, db: Session = Depends(get_db)):
    if db.query(models.Streamer).filter_by(twitch_id=s.twitch_id).first():
        raise HTTPException(status_code=400, detail="Streamer already exists")
    st = models.Streamer(**s.dict())
    db.add(st); db.commit(); db.refresh(st)
    return st

@app.get("/streamers/", response_model=list[schemas.Streamer])
def list_streamers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Streamer).offset(skip).limit(limit).all()

@app.get("/report/clips")
def get_clips_report(
    min_followers: int = Query(1000, description="Min. liczba followers"),
    min_views:     int = Query(30,   description="Min. liczba wyświetleń klipa"),
    skip:          int = Query(0,    ge=0, description="Ile pominąć (offset)"),
    limit:         int = Query(100,  gt=0, description="Ile pobrać (limit)"),
):
    # 1) pobierz streamerów (tylko ci z >= min_followers)
    streamers = twitch_api.fetch_streamers(min_followers)
    ids       = [s["id"] for s in streamers]

    # 2) pobierz klipy ostatnich 24h dla tych streamerów
    clips = twitch_api.fetch_clips(ids, min_views)

    # 3) sortuj malejąco po wyświetleniach i paginuj
    sorted_clips = sorted(clips, key=lambda c: c["views"], reverse=True)
    page         = sorted_clips[skip : skip + limit]

    # 4) statystyki podsumowujące
    total         = len(sorted_clips)
    top_streamers = [name for name,_ in Counter(c["broadcaster"] for c in clips).most_common(3)]
    top_games     = [gid  for gid, _ in Counter(c.get("game_id","") for c in clips).most_common(3)]

    return JSONResponse({
        "total_clips":   total,
        "top_streamers": top_streamers,
        "top_games":     top_games,
        "clips":         page
    })