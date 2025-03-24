from sqlalchemy import Integer, and_, func, insert, select, text, update
from sqlalchemy.orm import aliased

from db.core.db import async_engine,async_session_factory
from db.models import School,Product,Conference,MasterClass,Students,Teacher
from db.models import Base
from functools import wraps
from fastapi import Request,Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

# def auth_required(func):
#     @wraps(func)
#     async def wrapper(request: Request, *args, **kwargs):
#         # Получаем учителя из запроса
#         teacher = await get_current_teacher(request)
        
#         if not teacher:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Требуется авторизация",
#             )
            
#         kwargs["teacher"] = teacher
#         return await func(*args, **kwargs)
        
#     return wrapper

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
    async def select_students():
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
            student_data = result.first()

            if student_data:
                return {
                    "status": "success",
                    "data": {
                        "id": student_data.Students.id,
                        "surname": student_data.Students.surname,
                        "name": student_data.Students.name,
                        "father_name": student_data.Students.father_name,
                        "school": student_data.school_name,
                        "project_name": student_data.product_name,
                        "grade": student_data.Students.grade
                    }
                }
            return {"status": "not_found", "message": "Студент не найден"}




    async def get_current_teacher(credentials: HTTPBasicCredentials = Depends(security)):
        async with async_session_factory() as session:
            # Ищем учителя по логину
            query = select(Teacher).where(Teacher.login == credentials.username)
            result = await session.execute(query)
            teacher = result.scalar_one_or_none()
            
            if not teacher:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Неверный логин или пароль",
                )
                
            # Проверяем пароль
            if not teacher.check_password(credentials.password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Неверный логин или пароль",
                )
                
            return teacher

    @staticmethod
    # @auth_required
    async def select_students_by_teacher_id(teacher: Teacher):
        async with async_session_factory() as session:
            query = select(Students).where(Students.id_teacher == teacher.id)
            result = await session.execute(query)
            students = result.scalars().all()
            
            return {
                "students": [s.to_dict() for s in students],
                "admin": "true" if teacher.admin else "false"
            }

    @staticmethod
    async def create_admin(log,password):
        async with async_session_factory() as session:
            new_teacher = Teacher(
                login="ivanov",
                admin=True
            )
            new_teacher.set_password("qwerty123")
            session.add(new_teacher)
            await session.commit()

    @staticmethod
    async def find_student_data_by_id(id):
        async with async_session_factory() as session:
            query = select(
                Students,
                School,
                Product,
                Conference
            ).join(
                School, Students.id_school == School.id
            ).join(
                Product, Students.id_product == Product.id
            ).outerjoin(
                Conference, Product.id_conference == Conference.id
            ).where(Students.id == 1)
            #TODO: catch errors and what if table data with join or outerjoin didnt find?

            result = await session.execute(query)
            # s = [student.to_dict() for student in result.scalars().all()]
            student_data = result.first()
            print(student_data.Product.product_name)
    
            if student_data:
                return {
                    "status": "success",
                    "data": {
                        "id": student_data.Students.id,
                        "surname": student_data.Students.surname,
                        "name": student_data.Students.name,
                        "father_name": student_data.Students.father_name,
                        "section": student_data.Product.section,
                        "project_name": student_data.Product.product_name,
                        "school": student_data.School.school_name,
                        "grade": student_data.Students.grade,
                        "date_time": student_data.Product.date_time,
                        "location": student_data.Product.location,
                        "url_scheme": student_data.Product.url_scheme,
                        # "conf_name": student_data.Conference.name,
                    }
                }
            return {"status": "not_found", "message": "Студент не найден"}

    @staticmethod
    async def get_master_classes():
        async with async_session_factory() as session:
            import datetime
            date_time = datetime.datetime.now()
            print(date_time)
            print('\n')
            #TODO: порешать вопросик с датами
            query = select(MasterClass).where(MasterClass.date_time == date_time)
            result = await session.execute(query)
            master_classes = result.scalars().all()
            mc_list = [master_class.to_dict() for master_class in master_classes]
            if mc_list:
                return mc_list
            return {"status": "not_found", "message": "Мастерклассы не найдены"}




