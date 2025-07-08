from databases import Database
from sqlalchemy import MetaData, create_engine

import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  # e.g. postgresql://user:password@localhost:5432/dbname

database = Database(DATABASE_URL)
metadata = MetaData()

# Optional: create an engine for creating tables via SQLAlchemy
engine = create_engine(DATABASE_URL)
