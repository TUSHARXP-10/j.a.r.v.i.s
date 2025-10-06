#!/usr/bin/env python3

import sqlite3
import os

def make_user_admin():
    """Directly update user role to admin in database"""
    print("🛠️ Making User Admin (Direct Database Update)")
    print("=" * 50)
    
    db_path = "backend/data/workflows.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("❌ Users table does not exist")
            return False
        
        # Check if admin_master user exists
        cursor.execute("SELECT id, username, role FROM users WHERE username = ?", ("admin_master",))
        user = cursor.fetchone()
        
        if not user:
            print("❌ admin_master user not found")
            return False
        
        print(f"Found user: ID={user[0]}, Username={user[1]}, Role={user[2]}")
        
        # Update role to admin
        cursor.execute("UPDATE users SET role = ? WHERE username = ?", ("admin", "admin_master"))
        conn.commit()
        
        # Verify the update
        cursor.execute("SELECT role FROM users WHERE username = ?", ("admin_master",))
        new_role = cursor.fetchone()[0]
        
        if new_role == "admin":
            print("✅ User role updated to admin successfully!")
            return True
        else:
            print(f"❌ Role update failed. Current role: {new_role}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    make_user_admin()