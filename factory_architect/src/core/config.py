import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    INPUT_FILE: str = "/app/data/input.json"
    OUTPUT_DIR: str = "/app/data/output"
    # Using user-available next-gen model
    MODEL_NAME: str = "gemini-2.5-flash-preview-09-2025"

    class Config:
        env_file = ".env"

settings = Settings()
