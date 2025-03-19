from sqlalchemy import Integer, and_, func, insert, select, text, update
from sqlalchemy.orm import aliased

from db.core.db import async_engine,async_session_factory
from db.models import School,Product,Conference,MasterClass,Students,Teacher
from db.models import Base


class AsyncORM:
    @staticmethod
    async def create_tables():
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    @staticmethod
    async def insert_students():
        async with async_session_factory() as session:
            worker_jack = Students(name="Jack")
            worker_michael = Students(name="Michael")
            session.add_all([worker_jack, worker_michael])
            # flush взаимодействует с БД, поэтому пишем await
            await session.flush()
            await session.commit()

    @staticmethod
    async def select_workers():
        async with async_session_factory() as session:
            query = select(Students)
            result = await session.execute(query)
            students = result.scalars().all()
            students_data = [student.to_dict() for student in students]
            print(f"{students_data=}")
            
            return students_data

    