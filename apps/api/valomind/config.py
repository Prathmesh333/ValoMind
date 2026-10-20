from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://valomind:localdev@localhost:5432/valomind"
    demo_synthetic: bool = True
    demo_access_token: SecretStr = SecretStr("")
