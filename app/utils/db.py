from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import Config
from ..models.models import Base

engine = create_engine(Config.DATABASE_URL)
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

def get_session():
    return Session()