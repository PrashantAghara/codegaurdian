from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str
    astra_db_application_token: str
    astra_db_api_endpoint: str
    github_app_id: str = ""
    github_app_private_key_path: str = ""
    github_app_private_key_b64: str = ""
    github_webhook_secret: str = ""
    github_pat: str = ""
    mcp_server_url: str = "http://127.0.0.1:8001/mcp"
    hf_token: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
