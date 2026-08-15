from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import sqlite3
import bcrypt
import jwt
from datetime import datetime, timedelta
import os

app = FastAPI()

# CORS - Allow everything for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_PATH = "auth.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# Create users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()
print("✅ Database initialized!")

SECRET_KEY = "your-secret-key-change-this-in-production"

# Models
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Routes
@app.get("/")
def root():
    return {"message": "API is running!"}

@app.get("/api/test")
def test():
    return {"status": "success", "message": "Backend is working!"}

@app.post("/api/auth/register")
def register(user: UserCreate):
    try:
        print(f"📝 Registering user: {user.email}")
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
        if cursor.fetchone():
            print(f"❌ Email already exists: {user.email}")
            return {"error": "Email already exists"}, 400
        
        # Hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(user.password.encode('utf-8'), salt)
        
        # Insert user
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (user.name, user.email, hashed.decode('utf-8'))
        )
        conn.commit()
        
        # Get the new user
        cursor.execute("SELECT id, name, email, is_active FROM users WHERE email = ?", (user.email,))
        new_user = cursor.fetchone()
        
        print(f"✅ User registered: {user.email}")
        
        return {
            "message": "User created successfully",
            "user": {
                "id": new_user[0],
                "name": new_user[1],
                "email": new_user[2],
                "is_active": bool(new_user[3])
            }
        }
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        return {"error": str(e)}, 500

@app.post("/api/auth/login")
def login(user: UserLogin):
    try:
        print(f"🔐 Login attempt: {user.email}")
        
        cursor.execute("SELECT id, name, email, password_hash, is_active FROM users WHERE email = ?", (user.email,))
        result = cursor.fetchone()
        
        if not result:
            print(f"❌ User not found: {user.email}")
            return {"error": "Invalid credentials"}, 401
        
        print(f"✅ User found: {result[1]} ({result[2]})")
        
        # Verify password
        if not bcrypt.checkpw(user.password.encode('utf-8'), result[3].encode('utf-8')):
            print(f"❌ Password incorrect for: {user.email}")
            return {"error": "Invalid credentials"}, 401
        
        print(f"✅ Password verified for: {user.email}")
        
        # Create token
        token = jwt.encode(
            {"sub": user.email, "exp": datetime.utcnow() + timedelta(days=7)}, 
            SECRET_KEY,
            algorithm="HS256"
        )
        
        print(f"✅ Token created for: {user.email}")
        print(f"📝 Token: {token[:50]}...")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": result[0],
                "name": result[1],
                "email": result[2],
                "is_active": bool(result[4])
            }
        }
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return {"error": str(e)}, 500

@app.get("/api/auth/me")
def get_me(token: str):
    try:
        print(f"🔑 Getting user from token: {token[:30]}...")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        
        print(f"📧 Email from token: {email}")
        
        cursor.execute("SELECT id, name, email, is_active FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User not found: {email}")
            return {"error": "User not found"}, 404
        
        print(f"✅ User found: {user[1]}")
        
        return {
            "id": user[0],
            "name": user[1],
            "email": user[2],
            "is_active": bool(user[3])
        }
    except jwt.ExpiredSignatureError:
        print("❌ Token expired")
        return {"error": "Token expired"}, 401
    except Exception as e:
        print(f"❌ Get user error: {str(e)}")
        return {"error": str(e)}, 401

if __name__ == "__main__":
    import uvicorn
    print("="*50)
    print("🚀 Starting Solar & Wind Intelligence API")
    print("📝 API running on: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("="*50)
    uvicorn.run(app, host="0.0.0.0", port=8000)