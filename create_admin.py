import os
from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    username = os.getenv("ADMIN_USERNAME", "admin")
    email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("ADMIN_PASSWORD", "password")

    if not User.query.filter_by(email=email).first():
        admin = User(
            username=username,
            email=email,
            role="admin",
            contact_preference="email",
            contact_details=email,
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user {username} created successfully.")
    else:
        print(f"Admin user with email {email} already exists.")
