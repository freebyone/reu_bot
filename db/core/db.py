from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
# import settings

async_engine = create_async_engine(
    url="postgresql+asyncpg://your_username:new_password@127.0.0.1:5432/your_database",
    echo=False,
).execution_options(schema_translate_map={None:"rea_bot"})

async_session_factory = async_sessionmaker(async_engine)

if __name__ == "__main__":
    """
    Check DB connection
    """
    username = 'your_username'
    password = 'new_password'
    host = '127.0.0.1'
    port = '32'
    database = 'your_database'

    connection_string = f'postgresql+psycopg2://{username}:{password}@127.0.0.1:5432/{database}'

    engine = create_engine(connection_string)

    with engine.connect() as connection:
        inspector = inspect(connection)

        schemas = inspector.get_schema_names()

        for schema in schemas:
            print(schema)