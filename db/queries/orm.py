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
            worker_michael = Students(name="Michael",surname="Xer",father_name="Yux")
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

    @staticmethod
    async def auth_student(name,surname,father_name):
        async with async_session_factory() as session:
            clean_surname = surname.strip().lower()
            clean_name = name.strip().lower()
            clean_father_name = father_name.strip().lower()
            print(clean_name,clean_surname,clean_father_name)
            query = select(
                Students,
                School.school_name,
                Product.product_name
            ).join(
                School, Students.id_school == School.id
            ).join(
                Product, Students.id_product == Product.id
            ).where(
                func.lower(Students.surname) == clean_surname,
                func.lower(Students.name) == clean_name,
                func.lower(Students.father_name) == clean_father_name
            )

            result = await session.execute(query)
            s = [student.to_dict() for student in result.scalars().all()]
            print(s)
            student_data = result.first()

            if student_data:
                return {
                    "status": "success",
                    "data": {
                        "fio": f"{student_data.Students.surname} "
                                f"{student_data.Students.name} "
                                f"{student_data.Students.father_name}",
                        "school": student_data.school_name,
                        "project": student_data.project_title,
                        "grade": student_data.Students.grade
                    }
                }
            return {"status": "not_found", "message": "Студент не найден"}


    