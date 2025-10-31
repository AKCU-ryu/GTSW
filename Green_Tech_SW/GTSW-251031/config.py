# config.py
import os

class Config:
    # 예: PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        # "sqlite:///local.db"  # 기본값(없으면 SQLite 로컬 파일)
        #
        # "SQLite: sqlite: // / local.db"
        #
        # "PostgreSQL: postgresql + psycopg2: // user: pw @ localhost:5432 / mydb"
        #
        # "MySQL: mysql + pymysql: // user: pw @ 127.0.0.1: 3306 / mydb"
    
        "Oracle(oracle + cx_oracle): oracle + cx_oracle: // user: pw @ localhost:1521 /?service_name = XE"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")  # 세션/CSRF용
