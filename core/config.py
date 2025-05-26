from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuration settings for the OpenVPN client management service.
    """
    # General settings
    log_level: str = "INFO"
    log_file: str = "ovpn_manager.log"

    # API settings
    api_key: str = ""
    api_host: str = ""
    api_port: int = 8000

    class Config:
        env_file = '.env'


settings = Settings()
