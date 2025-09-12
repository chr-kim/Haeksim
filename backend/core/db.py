# backend/core/db.py
from sqlalchemy import create_engine, MetaData
import databases
from .config import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = MetaData()
engine = create_engine(DATABASE_URL)