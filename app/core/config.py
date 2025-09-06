from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    MONGO_URI: str = Field(default="mongodb://localhost:27017", env="MONGO_URI")
    DB_NAME: str = Field(default="main", env="DB_NAME")

    SECRET_KEY: str = Field(default="supersecret", env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    SENDGRID_API_KEY: str = Field(env='SENDGRID_API_KEY')
    SENDGRID_FROM_EMAIL: str = Field(env='SENDGRID_FROM_EMAIL')
    S3_ENDPOINT: str = Field(env='S3_ENDPOINT')
    S3_REGION: str = Field(env='S3_REGION')
    S3_BUCKET: str = Field(env='S3_BUCKET')
    S3_ACCESS_KEY_ID: str = Field(env='S3_ACCESS_KEY_ID')
    S3_SECRET_ACCESS_KEY: str = Field(env='S3_SECRET_ACCESS_KEY')
    ALLOWED_ORIGIN: str = Field(env='ALLOWED_ORIGIN')

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
