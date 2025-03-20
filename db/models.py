from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sql
from sqlalchemy.orm import class_mapper
from datetime import datetime

Base = declarative_base()

class School(Base):
    __tablename__ = 'schools'
    id = sql.Column(sql.Integer, primary_key=True)
    school_name = sql.Column(sql.String(1024))


class Product(Base):
    __tablename__ = 'products'
    id = sql.Column(sql.Integer, primary_key=True)
    section = sql.Column(sql.String(1024))
    product_name = sql.Column(sql.String(1024))
    date_time = sql.Column(sql.DateTime, default=datetime.now)
    id_school = sql.Column(sql.Integer, sql.ForeignKey('schools.id', ondelete="CASCADE"))
    location = sql.Column(sql.String(1024))
    url_scheme = sql.Column(sql.String(1024))
    id_conference = sql.Column(sql.Integer, sql.ForeignKey('conference.id_conference', ondelete="CASCADE"))

class Conference(Base):
    __tablename__ = 'conference'
    id_conference = sql.Column(sql.Integer, primary_key=True)
    name = sql.Column(sql.String(1024))
    date = sql.Column(sql.Date)
    time = sql.Column(sql.Time)

class MasterClass(Base):
    __tablename__ = 'master_class'
    id_master_class = sql.Column(sql.Integer, primary_key=True)
    name = sql.Column(sql.String(1024))
    time = sql.Column(sql.Time)
    url_link = sql.Column(sql.String(1024))
    id_conference = sql.Column(sql.Integer, sql.ForeignKey('conference.id_conference', ondelete="CASCADE"))

class Students(Base):
    __tablename__ = "students"
    id = sql.Column(sql.Integer, primary_key=True)
    
    surname = sql.Column(sql.String(1024))
    name = sql.Column(sql.String(1024))
    father_name = sql.Column(sql.String(1024))
    grade = sql.Column(sql.Integer)
    
    id_school = sql.Column(sql.Integer, sql.ForeignKey('schools.id', ondelete="CASCADE"))
    id_product = sql.Column(sql.Integer, sql.ForeignKey('products.id', ondelete="CASCADE"))

    def to_dict(self):
        """Конвертирует объект в словарь."""
        return {c.key: getattr(self, c.key) for c in class_mapper(self.__class__).columns}

class Teacher(Base):
    __tablename__ = "teachers"
    id = sql.Column(sql.Integer, primary_key=True)
    
    surname = sql.Column(sql.String(1024))
    name = sql.Column(sql.String(1024))
    father_name = sql.Column(sql.String(1024))
    grade = sql.Column(sql.Integer)
    
    id_school = sql.Column(sql.Integer, sql.ForeignKey('schools.id', ondelete="CASCADE"))
    
    login = sql.Column(sql.String(1024))
    password = sql.Column(sql.String(1024))
    admin = sql.Column(sql.Boolean, default=False)
