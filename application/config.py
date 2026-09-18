from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

'''
Pydantic class to contain the environment variables needed for the project
'''
class Settings(BaseSettings):
    debug: bool = True
    connection_str: str = ""
    secret_key: str = ""
    access_token_expire_minutes: int = 30
    hashing_algo: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env")


'''
Method which can be used to get settings from anywhere in the project.
Using 'lru_cache' the settings object only gets created once, then can be used repeatedly when it's needed.
'''
@lru_cache
def get_settings():
        return Settings()


