from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str
    astra_db_application_token: str
    astra_db_api_endpoint: str
    astra_db_keyspace: str = ""
    database_url: str
    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_host: str = "https://cloud.langfuse.com"
    github_app_id: str = ""
    github_app_private_key_path: str = ""
    github_webhook_secret: str = ""
    github_pat: str = ""
    hf_token: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
