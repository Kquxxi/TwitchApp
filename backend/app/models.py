from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base
from datetime import datetime

class Streamer(Base):
    __tablename__ = "streamers"

    id             = Column(Integer, primary_key=True, index=True)
    twitch_id      = Column(String, unique=True, nullable=False, index=True)
    login          = Column(String, unique=True, nullable=False)
    display_name   = Column(String, nullable=False)
    follower_count = Column(Integer, nullable=False, default=0)
    created_at     = Column(DateTime, default=datetime.utcnow)
