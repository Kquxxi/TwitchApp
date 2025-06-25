from pydantic import BaseModel

class StreamerBase(BaseModel):
    twitch_id: str
    login: str
    display_name: str
    follower_count: int

class StreamerCreate(StreamerBase):
    pass

class Streamer(StreamerBase):
    id: int

    class Config:
        orm_mode = True
