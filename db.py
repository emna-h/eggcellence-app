import os
import pyodbc
from pathlib import Path
from dotenv import load_dotenv

# Force load .env from the exact directory of this script
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)


def get_db_connection():
    server = os.getenv('DB_SERVER', r'DESKTOP-F198VRM\SQLEXPRESS')
    database = os.getenv('DB_NAME', 'EggcellenceDB')
    user = os.getenv('DB_USER', 'sa')
    password = os.getenv('DB_PASSWORD', '')

    db_config = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(db_config)


def row_to_dict(cursor, row):
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))
