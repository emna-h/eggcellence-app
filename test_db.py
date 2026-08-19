import os
import pyodbc
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

print("=== LOADED .ENV VARIABLES ===")
print(f"  DB_SERVER:   {os.getenv('DB_SERVER')}")
print(f"  DB_NAME:     {os.getenv('DB_NAME')}")
print(f"  DB_USER:     {os.getenv('DB_USER')}")
print(f"  DB_PASSWORD: {os.getenv('DB_PASSWORD')}")