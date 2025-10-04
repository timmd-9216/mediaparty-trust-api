from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Config(BaseSettings):
    app_name: str = "MediaPartyTrustAPI"
    debug: bool = False


config = Config()
