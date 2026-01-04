from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    MODEL_NAME: str = "gemini-2.0-flash-exp" # Or your preferred model

    class Config:
        env_file = ".env"
        extra = "ignore" 

settings = Settings()