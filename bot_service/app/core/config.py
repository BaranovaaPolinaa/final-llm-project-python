from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "bot-service"
    ENV: str = "local"

    JWT_SECRET: str = "change_me_super_secret"
    JWT_ALG: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
