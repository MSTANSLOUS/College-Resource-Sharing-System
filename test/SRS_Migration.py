import os
import psycopg2

DATABASE_URL = "postgresql://student_resources_user:9fIQlfOewC5CkvvPZ1Q7fA5JGoGqQyWd@dpg-d9bo5ofavr4c73b60pig-a.virginia-postgres.render.com/student_resources"

def increase_title_length():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()

        # Check current column type (optional)
        cur.execute("""
            SELECT data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name='resource' AND column_name='title';
        """)
        result = cur.fetchone()
        print(f"Current type: {result}")

        # Alter column to VARCHAR(300)
        cur.execute('ALTER TABLE resource ALTER COLUMN title TYPE VARCHAR(300);')
        print("✅ Title column length increased to 300 characters.")

        cur.close()
        conn.close()
        print("✨ Migration complete!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    confirm = input("⚠️ This will increase the title column length to 300. Continue? (yes/no): ")
    if confirm.lower() == 'yes':
        increase_title_length()
    else:
        print("Operation cancelled.")