import os
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine

DB_URL = os.getenv("DB_URL")
print(DB_URL)

engine = create_engine(
    DB_URL,
    echo=True
)

if __name__ == "__main__":
    with engine.connect() as conn:
        print("DB connected")