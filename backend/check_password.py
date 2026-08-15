import sqlite3
import bcrypt

email = "test@example.com"
password = "password123"  # The password you're trying

conn = sqlite3.connect('auth.db')
cursor = conn.cursor()

cursor.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
result = cursor.fetchone()

if result:
    stored_hash = result[0]
    print(f"Stored hash: {stored_hash}")
    print(f"Testing password: {password}")
    
    # Check if password matches
    if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
        print("✅ Password matches!")
    else:
        print("❌ Password does NOT match!")
else:
    print(f"❌ User {email} not found")