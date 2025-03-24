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
    """Основная функция обработки данных (все этапы)"""
    try:
        # Загрузка всех листов Excel
        df_projects = pd.read_excel(
            "file.xlsx",
            sheet_name="Проекты",  # Предполагаемое имя листа
            header=0,
            names=[
                "Секция", "Название проекта", "Школа", "Класс", "Формат выступления",
                "Дата_время", "Слот", "Лидер проекта", "Школа_лидера", 
                "Участник 1", "Школа_уч1", "Участник 2", "Школа_уч2", "Аудитория"
            ]
        )

        df_conferences = pd.read_excel(
            "file.xlsx",
            sheet_name="Конференции",
            header=0,
            names=["Название", "Дата_время"]
        )
        
        df_masterclass = pd.read_excel(
            "file.xlsx",
            sheet_name="МК",
            header=0,
            names=["Название", "Время_день", "Ссылка", "Локация", "Конференция"]
        )

        df_teachers = pd.read_excel(
            "file.xlsx",
            sheet_name="Учителя",
            header=0,
            names=["ФИО", "Школа"]
        )

        async with session.begin():
            # 1. Обработка конференций
            conference_cache = {}
            for idx, row in df_conferences.iterrows():
                conference = Conference(
                    name=row['Название'],
                    date_time=pd.to_datetime(row['Дата_время'])
                )
                session.add(conference)
                await session.flush()
                conference_cache[row['Название']] = conference.id

            # 2. Обработка мастер-классов
            masterclass_cache = {}
            for idx, row in df_masterclass.iterrows():
                conference_id = conference_cache.get(row['Конференция'])
                if not conference_id:
                    raise ValueError(f"Конференция {row['Конференция']} не найдена")

                masterclass = MasterClass(
                    name=row['Название'],
                    time=pd.to_datetime(row['Время_день']),
                    url=row['Ссылка'],
                    location=row['Локация'],
                    conference_id=conference_id
                )
                session.add(masterclass)
                await session.flush()
                masterclass_cache[row['Название']] = masterclass.id

            # 3. Обработка учителей (оригинальный кэш школ)
            school_cache = {}
            for idx, row in df_teachers.iterrows():
                school_id = await get_or_create_school(
                    session,
                    row['Школа'],
                    school_cache
                )
                
                surname, name, father_name = parse_fio(row['ФИО'])
                teacher = Teacher(
                    surname=surname,
                    name=name,
                    father_name=father_name,
                    id_school=school_id
                )
                session.add(teacher)

            # 4. Оригинальная обработка проектов и студентов 
            school_cache_projects = {}
            product_cache = {}
            
            # Первый проход: проекты
            for idx, row in df_projects.iterrows():
                school_id = await get_or_create_school(
                    session,
                    row['Школа_лидера'],
                    school_cache_projects
                )

                product = Product(
                    section=row['Секция'],
                    product_name=row['Название проекта'],
                    date_time=pd.to_datetime(row['Дата_время']),
                    id_school=school_id,
                    location=row['Аудитория']
                )
                session.add(product)
                await session.flush()
                product_cache[row['Название проекта']] = product.id

            # Второй проход: студенты
            for idx, row in df_projects.iterrows():
                product_id = product_cache.get(row['Название проекта'])
                if not product_id:
                    continue

                school_id = school_cache_projects.get(row['Школа_лидера'])
                if not school_id:
                    continue

                students_data = []
                for role in ['Лидер проекта', 'Участник 1', 'Участник 2']:
                    fio = row[role]
                    if pd.isna(fio):
                        continue

                    surname, name, father_name = parse_fio(fio)
                    students_data.append({
                        "surname": surname,
                        "name": name,
                        "father_name": father_name,
                        "grade": row['Класс'],
                        "id_school": school_id,
                        "id_product": product_id
                    })

                if students_data:
                    await session.execute(insert(Students), students_data)

    except Exception as e:
        logging.error(f"Ошибка: {str(e)}")
        await session.rollback()
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

   
    