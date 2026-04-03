from app import create_app  # Or however you initialize your app (e.g., from app import app)
from app.models import db, Program

# 1. Initialize your app so Flask knows where to look
app = create_app()

# 2. Wrap everything in the app context
with app.app_context():
    # Define your school's programs
    programs_list = ['BMIS', 'BBME', 'BAAA-IS', 'BMPR', 'BBFSM']

    # Loop and add them if they don't already exist
    for prog_name in programs_list:
        exists = Program.query.filter_by(name=prog_name).first()
        if not exists:
            new_prog = Program(name=prog_name)
            db.session.add(new_prog)

    # Save everything to the database
    db.session.commit()

    print("All programs seeded successfully!")