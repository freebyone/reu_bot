import pandas as pd
from sqlalchemy import select,insert
from sqlalchemy.orm import query
import sqlalchemy as sql
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import asyncio
from db.models import School, Product, Students, Base
from db.core.db import async_session_factory,async_engine
import logging
from sqlalchemy.exc import SQLAlchemyError


async def clear_database(engine: AsyncSession, Base):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        #TODO: сделать сброс айдишек для автоинкремента
    
async def get_or_create_school(session: AsyncSession, school_name: str, cache: dict) -> int:
    """Создает или возвращает существующую школу"""
    if not school_name:
        return None
    
    school_name = str(school_name).strip()
    if not school_name:
        return None
    print(f"PRIONTIRNT: {school_name}\n\n --- {cache}")
    if school_name in cache:
        return cache[school_name]
    
    result = await session.execute(select(School).where(School.school_name == school_name))
    school = result.scalars().first()
    if not school:
        school = School(school_name=school_name)
        session.add(school)
        await session.flush()
        # await session.commit()
        
    
    cache[school_name] = school.id
    return school.id

def parse_fio(fio: str) -> tuple:
    """Парсит ФИО на составляющие с обработкой пустых значений"""
    if pd.isna(fio):
        return None, None, None
        
    parts = str(fio).strip().split()
    return (
        parts[0] if len(parts) > 0 else None,
        parts[1] if len(parts) > 1 else None,
        ' '.join(parts[2:]) if len(parts) > 2 else None
    )

async def process_data(session: AsyncSession):
    """Основная функция обработки данных"""
    try:
        df = pd.read_excel("file.xlsx", header=0, names=[
            "Секция", "Название проекта", "Школа", "Класс", "Формат выступления", 
            "Дата_время", "Слот", "Лидер проекта", "Школа_лидера", "Участник 1", 
            "Школа_уч1", "Участник 2", "Школа_уч2", "Аудитория"
        ])

        # Предварительная обработка данных
        df = df.dropna(subset=["Школа_лидера", "Название проекта"])
        df["Дата_время"] = pd.to_datetime(df["Дата_время"], errors="coerce")

        async with session.begin():  # Главная транзакция
            school_cache = {}
            product_cache = {}

            # Первый проход: создание школ и продуктов
            for idx, row in df.iterrows():
                try:
                    school_name = row['Школа_лидера']
                    school_id = await get_or_create_school(session, school_name, school_cache)

                    product = Product(
                        section=row['Секция'],
                        product_name=row['Название проекта'],
                        # date_time=row['Дата_время'],
                        id_school=school_id,
                        location=str(row['Аудитория'])
                    )
                    session.add(product)
                    await session.flush()
                    product_cache[row['Название проекта']] = product.id

                except Exception as e:
                    logging.error(f"Ошибка в строке {idx}: {str(e)}")
                    raise  # Прерываем транзакцию

            # Второй проход: создание участников
            for idx, row in df.iterrows():
                try:
                    product_id = product_cache.get(row['Название проекта'])
                    if not product_id:
                        continue

                    school_id = school_cache.get(row['Школа_лидера'])
                    if not school_id:
                        raise ValueError(f"Школа '{row['Школа_лидера']}' не найдена")

                    students = []
                    for role in ['Лидер проекта', 'Участник 1', 'Участник 2']:
                        fio = row[role]
                        if pd.isna(fio):
                            continue

                        surname, name, father_name = parse_fio(fio)
                        
                        students.append({
                            "surname": surname,
                            "name": name,
                            "father_name": father_name,
                            "grade": int(row['Класс']) if pd.notna(row['Класс']) else None,
                            "id_school": school_id,
                            "id_product": product_id
                        })
                    #await session.execute(query(Students).add_all(students))
                    # Пакетная вставка студентов
                    if students:
                        await session.execute(
                            insert(Students),
                            students
                        )
                        
                except Exception as e:
                    logging.error(f"Ошибка в строке {idx}: {str(e)}")
                    raise

    except SQLAlchemyError as e:
        logging.error(f"Ошибка базы данных: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Общая ошибка: {str(e)}")
        raise

async def main():
    try:
        # Очистка и инициализация БД
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        
        # Основной процесс
        async with async_session_factory() as session:
            await process_data(session)
            
    except Exception as e:
        logging.critical(f"Критическая ошибка: {str(e)}")
    finally:
        await async_engine.dispose()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler()
        ]
    )
    asyncio.run(main())
    # Настройка подключения (замените параметры на свои)
    # async_engine = create_async_engine(
    #     "postgresql+asyncpg://user:password@localhost/dbname",
    #     echo=True  # Включить для отладки SQL-запросов
    # )
    # async_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)

   
    