from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from redis.asyncio import Redis
from aiogram.fsm.storage.redis import RedisStorage


class BotSettings(BaseSettings):
    token: str
    admin_ids: list[int] = []
    
    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value):
        if isinstance(value, str):
            return [int(x.strip()) for x in value.split(",") if x.strip()]
        if isinstance(value, int):
            return [value]
        if isinstance(value, list):
            return value
        return []


class DatabaseSettings(BaseSettings):
    name: str 
    host: str
    port: int
    user: str
    password: str

class RedisSettings(BaseSettings):
    host: str
    port: int 
    db: int 
    username: str = ""
    password: str = ""
    
    def get_redis(self) -> Redis:
        return Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            decode_responses=True
        )
        
    def get_redis_storage(self) -> RedisStorage:
        return RedisStorage(redis=self.get_redis())



class Config(BaseSettings):
    bot: BotSettings 
    db: DatabaseSettings 
    redis: RedisSettings
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
        "env_nested_delimiter": "__"
    }


def load_config(env_path: str | None = None) -> Config:
    return Config(_env_file=env_path or ".env")

