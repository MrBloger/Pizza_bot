from sqlalchemy.engine import URL
from config.config import load_config

def get_db_url() -> URL:
    config = load_config()
    db = config.db
    return URL.create(
        drivername="postgresql+asyncpg",
        username=db.user,
        password=db.password,
        host=db.host,
        port=db.port,
        database=db.name
    )