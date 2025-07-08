from database import engine, metadata
from models import user_profiles

metadata.create_all(engine)

print("Tables created successfully.")
