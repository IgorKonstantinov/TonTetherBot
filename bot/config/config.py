from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str

    RANDOM_TAPS_COUNT: list[int] = [50, 100]
    SLEEP_BETWEEN_TAP: list[int] = [5, 10]
    RANDOM_SLEEP: list[int] = [1, 5]

    MIN_AVAILABLE_CLICKS: int = 100
    SLEEP_BY_MIN_CLICKS: list[int] = [300, 600]

    AUTO_UPGRADE: bool = True
    MAX_LEVEL: int = 20
    BALANCE_TO_SAVE: int = 100000

    APPLY_DAILY_BOOST: bool = False
    USE_PROXY_FROM_FILE: bool = False

settings = Settings()
