import sys
from app import create_app  # Or from app import app if not using a factory
from app.models import db, User


def promote_to_rep(email):
    app = create_app()
    with app.app_context():
        # Look up the student by their email
        user = User.query.filter_by(email=email).first()

        if not user:
            print(f"Error: No user found with the email '{email}'")
            return

        # Elevate privileges and auto-approve them
        user.is_class_rep = True
        user.is_approved = True

        db.session.commit()
        print(f"Success! {user.full_name} is now an approved Class Representative.")


if __name__ == "__main__":
    # You can pass the email in the terminal, or just hardcode it here
    if len(sys.argv) > 1:
        target_email = sys.argv[1]
    else:
        target_email = "grace@gmail.com"  # <-- Change this to your test user's email!

    promote_to_rep(target_email)