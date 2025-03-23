from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
# import settings

async_engine = create_async_engine(
    url="postgresql+asyncpg://postgres:admin@127.0.0.1:5432/reu_db",
    echo=False,
).execution_options(schema_translate_map={None:"reu_bot"})

async_session_factory = async_sessionmaker(async_engine)

if __name__ == "__main__":
    """
    Check DB connection
    """
    username = 'postgres'
    password = 'admin'
    host = '127.0.0.1'
    port = '5432'
    database = 'reu_db'

    connection_string = f'postgresql+psycopg2://{username}:{password}@127.0.0.1:5432/{database}'

    engine = create_engine(connection_string)

    with engine.connect() as connection:
        inspector = inspect(connection)

        schemas = inspector.get_schema_names()

        for schema in schemas:
            print(schema)