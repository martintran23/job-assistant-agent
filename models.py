from sqlalchemy import Table, Column, Integer, String, Text
from database import metadata

user_profiles = Table(
    "user_profiles",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("full_name", String(length=100), nullable=False),
    Column("email", String(length=100), nullable=False, unique=True),
    Column("phone", String(length=20), nullable=True),
    Column("work_history", Text, nullable=True),
    Column("education", Text, nullable=True),
)
