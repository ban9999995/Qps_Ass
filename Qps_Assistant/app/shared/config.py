"""集中管理环境变量与运行时配置。"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用运行配置，所有外部服务参数均可由环境变量覆盖。"""

    app_name: str = "电商运营助手"
    app_env: str = "development"
    debug: bool = True
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:5173"
    database_url: str = "sqlite+aiosqlite:///./qps_demo.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    data_dir: str = "./data"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    vlm_base_url: str = ""
    vlm_api_key: str = ""
    image_generation_base_url: str = ""
    image_generation_api_key: str = ""
    video_generation_base_url: str = ""
    video_generation_api_key: str = ""
    model_timeout_seconds: int = 60
    task_timeout_seconds: int = 600
    task_max_retries: int = 3
    task_poll_seconds: int = 3
    log_level: str = "INFO"

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_flag(cls, value: object) -> object:
        """兼容开发环境可能注入的 release/debug 字符串。"""
        if isinstance(value, str) and value.lower() in {"release", "prod", "production"}:
            return False
        return value

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        """将逗号分隔的跨域地址转换成列表。"""
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    """返回进程级缓存配置实例。"""
    return Settings()
