from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    app_name: str = "MediaPartyTrustAPI"
    debug: bool = False


config = Config()
