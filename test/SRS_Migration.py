import os
import psycopg2
import shutil

DATABASE_URL = "postgresql://student_resources_user:9fIQlfOewC5CkvvPZ1Q7fA5JGoGqQyWd@dpg-d9bo5ofavr4c73b60pig-a.virginia-postgres.render.com/student_resources"

def delete_all_resources():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()

        # 1. Delete associations first (foreign key constraint)
        cur.execute('DELETE FROM resource_programs;')
        print("✅ Removed all resource-program associations.")

        # 2. Delete all resource records
        cur.execute('DELETE FROM resource;')
        print("✅ All resource records deleted from database.")

        # 3. (Optional) Delete physical files from static/uploads
        upload_folder = os.path.join(os.getcwd(), 'static', 'uploads')
        if os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                file_path = os.path.join(upload_folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"⚠️ Could not delete {file_path}: {e}")
            print("✅ All uploaded files deleted from static/uploads.")
        else:
            print("ℹ️ Upload folder not found, skipping file deletion.")

        cur.close()
        conn.close()
        print("✨ Clean‑up complete!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    confirm = input("⚠️ This will delete ALL resources (including files). Are you sure? (yes/no): ")
    if confirm.lower() == 'yes':
        delete_all_resources()
    else:
        print("Operation cancelled.")