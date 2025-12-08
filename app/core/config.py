from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    KAVENEGAR_API_KEY: str
    KAVENEGAR_OTP_TEMPLATE: str

    class Config:
        env_file = ".env"

settings = Settings()
