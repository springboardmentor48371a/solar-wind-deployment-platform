
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "renewable.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Renewable Energy Planner',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        region TEXT NOT NULL,
        technology TEXT NOT NULL DEFAULT 'Hybrid Solar + Wind',
        status TEXT NOT NULL DEFAULT 'Planning',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS sites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        region TEXT NOT NULL,
        land_area REAL NOT NULL DEFAULT 0,
        elevation REAL NOT NULL DEFAULT 0,
        infrastructure TEXT NOT NULL DEFAULT 'Moderate',
        land_ownership TEXT NOT NULL DEFAULT 'Private',
        solar_irradiance REAL NOT NULL DEFAULT 5.0,
        wind_speed REAL NOT NULL DEFAULT 6.0,
        wind_direction REAL NOT NULL DEFAULT 180,
        temperature REAL NOT NULL DEFAULT 25,
        rainfall REAL NOT NULL DEFAULT 700,
        cloud_cover REAL NOT NULL DEFAULT 30,
        slope REAL NOT NULL DEFAULT 5,
        vegetation_index REAL NOT NULL DEFAULT 0.4,
        roads_distance REAL NOT NULL DEFAULT 5,
        transmission_distance REAL NOT NULL DEFAULT 10,
        protected_zone INTEGER NOT NULL DEFAULT 0,
        water_body INTEGER NOT NULL DEFAULT 0,
        agricultural_land INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    conn.close()
