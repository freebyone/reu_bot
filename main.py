import asyncio
import os
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

current_file_path = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(os.path.dirname(current_file_path))
sys.path.insert(0, PROJECT_ROOT)
# sys.path.insert(1, os.path.join(sys.path[0], '..'))

from db.queries.orm import AsyncORM
from pydantic import BaseModel

class StudentAuthRequest(BaseModel):
    name: str
    surname: str
    father_name: str


def create_fastapi_app():
    app = FastAPI(title="FastAPI")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
        
        
    @app.get("/students")
    async def get_resumes():
        resumes = await AsyncORM.select_workers()
        return resumes
    
    @app.post("/auth_student")
    async def auth_student(request: StudentAuthRequest):
        return await AsyncORM.auth_student(**request.dict())
    
    return app
    

app = create_fastapi_app()

async def main():
    await AsyncORM.create_tables()
    await AsyncORM.insert_students()
    await AsyncORM.select_workers()


if __name__ == "__main__":
    if "--webserver" in sys.argv:
        uvicorn.run(
            app="main:app",  # Используем текущий файл
            host="0.0.0.0",
            port=8000,
            reload=True
        )
    else:
        asyncio.run(main())