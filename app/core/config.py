from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'BotNutri MVP'
    bot_token: str = Field(default='changeme')
    openai_api_key: str = Field(default='changeme')
    base_url: str = Field(default='http://localhost:8000')
    db_url: str = Field(default='sqlite:///./botnutri.db')


settings = Settings()
