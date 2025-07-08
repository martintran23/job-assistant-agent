from database import database, metadata
from models import user_profiles
import asyncio
from sqlalchemy import create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

metadata.create_all(engine)
print("Tables created successfully.")
