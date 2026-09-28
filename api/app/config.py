from dotenv import load_dotenv
load_dotenv()
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    webhook_secret: str
    reservation_ttl_minutes: int = 5

settings = Settings()  # type: ignore[call-arg]