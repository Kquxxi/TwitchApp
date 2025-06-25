from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

class Settings(BaseSettings):
    database_url: str

    model_config = SettingsConfigDict(
        env_file=str(env_path),
        extra="ignore"      # <-- tutaj pozwalamy na wszystkie inne ENV-y
    )

settings = Settings()
