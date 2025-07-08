from databases import Database
from sqlalchemy import MetaData, create_engine

import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Async database connection via databases package
database = Database(DATABASE_URL)

# SQLAlchemy engine and metadata for table creation and ORM
engine = create_engine(DATABASE_URL)
metadata = MetaData()
