import os
import psycopg2

# Your Render PostgreSQL connection string
DATABASE_URL = "postgresql://student_resources_user:9fIQlfOewC5CkvvPZ1Q7fA5JGoGqQyWd@dpg-d9bo5ofavr4c73b60pig-a.virginia-postgres.render.com/student_resources"

try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute('ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(256);')
    print("✅ Column altered successfully!")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")