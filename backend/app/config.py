from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Auto-injected by Databricks Apps runtime; set manually for local dev
    databricks_host: str = ''
    databricks_token: str = ''

    databricks_warehouse_id: str = '5288ab7cd99c4e09'
    databricks_catalog: str = 'main'

    api_host: str = '0.0.0.0'
    api_port: int = 8000
    cors_origins: str = 'http://localhost:5173'

    # extra='ignore' lets the SDK pick up DATABRICKS_AZURE_* vars directly without pydantic rejecting them
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(',')]


settings = Settings()
