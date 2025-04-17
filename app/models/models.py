from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    full_name = Column(String)
    phone_number = Column(String)
    instagram_username = Column(String)
    instagram_password = Column(String)
    lang = Column(String, default='en')
    balance = Column(Integer, default=0)

class Content(Base):
    __tablename__ = 'contents'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    content = Column(String)

class Image(Base):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    image_id = Column(String)

class ScheduledPost(Base):
    __tablename__ = 'scheduled_posts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    file_path = Column(String)  
    time = Column(DateTime)
    caption = Column(String)
    content_type = Column(String)

class Feedback(Base):
    __tablename__ = 'feedbacks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    feedback = Column(String, nullable=False)