from sqlalchemy import Table, Column, Integer, String, Text
from database import metadata

# User profiles table
user_profiles = Table(
    "user_profiles",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("full_name", String, nullable=False),
    Column("email", String, nullable=False, unique=True),
    Column("phone", String, nullable=True),
    Column("work_history", Text, nullable=True),
    Column("education", Text, nullable=True),
)

# Resumes table
resumes = Table(
    "resumes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("filename", String, nullable=False),
    Column("content", Text, nullable=False),
)
