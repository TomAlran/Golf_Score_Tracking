# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Courses(Base):
    __tablename__ = "courses"
    course_id = Column(String, primary_key = True)
    name = Column(String)
    sss = Column(Float)
    slope = Column(Integer)
    distance = Column(Integer)
    holes = relationship("Holes", backref=backref("course"))
    
class Holes(Base):
    __tablename__ = "holes"
    hole_id = Column(String, primary_key = True)
    course_id = Column(String, ForeignKey("courses.course_id"))
    number = Column(Integer)
    par = Column(Integer)
    distance = Column(Integer)
    hcp = Column(Integer)
    
class Scorecard(Base):
    __tablename__ = "scorecard"
    id = Column(Integer, primary_key = True)
    scorecard_id = Column(String)
    date = Column(Date)
    hole_id = Column(String, ForeignKey("holes.hole_id"))
    score = Column(Integer)
    fairway = Column(String)
    putts = Column(Integer)
    bunker = Column(Integer)
    water = Column(Integer)
    penalty = Column(Integer)
