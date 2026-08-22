from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import sqlite3
import bcrypt
import jwt
from datetime import datetime, timedelta
import os
import json
import requests
import numpy as np
from typing import Dict, Any, List, Optional  # <--- ADDED Optional

# ============================================
# APP INITIALIZATION
# ============================================
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# DATABASE SETUP (SQLite)
# ============================================
conn = sqlite3.connect('auth.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    role TEXT DEFAULT 'planner',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

cursor.execute('''
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    description TEXT,
    technology TEXT NOT NULL,
    budget REAL DEFAULT 0,
    status TEXT DEFAULT 'DRAFT',
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

cursor.execute('''
CREATE TABLE IF NOT EXISTS sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    site_name TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    region TEXT,
    land_area REAL,
    elevation REAL,
    land_ownership TEXT,
    existing_infrastructure TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

# (The rest of the tables like environmental_data, solar_assessments, etc. are created here, just keep them exactly as they were in your original code!)

# ============================================
# PYDANTIC MODELS
# ============================================
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "planner"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ProjectCreate(BaseModel):
    project_name: str
    description: str = None
    technology: str = "SOLAR"
    budget: float = 0.0

# *** THE CRITICAL FIX IS HERE ***
class SiteCreate(BaseModel):
    project_id: Optional[int] = None  # <--- Changed to Optional
    site_name: str
    latitude: float
    longitude: float
    region: str = None
    land_area: float = None
    elevation: float = None
    land_ownership: str = None
    existing_infrastructure: str = None

# (Keep the rest of your original code - Geocode, Solar, Wind, Suitability, etc. exactly as you had it!)

# ============================================
# RUN APP
# ============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)