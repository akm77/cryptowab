from pydantic import BaseSettings, SecretStr


class Settings(BaseSettings):
    bot_token: SecretStr
    admins: list[int]
    use_redis: bool

    redis_host: str
    redis_port: int
    redis_db: int
    redis_password: SecretStr

    db_dialect: str
    db_user: str
    pg_password: SecretStr
    db_pass: SecretStr
    db_host: str
    db_name: str
    db_echo: bool

    class Config:
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name == 'admins':
                return [int(x) for x in raw_val.split(',')]
            return cls.json_loads(raw_val)

        env_file = '.env'
        env_file_encoding = 'utf-8'


config = Settings()
