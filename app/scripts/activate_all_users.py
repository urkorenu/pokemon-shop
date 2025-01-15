from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models import User
import os

# Replace with your database connection string
DATABASE_URI = (
    f"postgresql+psycopg2://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)

# Create a database engine
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()


def activate_all_users():
    try:
        # Query all users
        users = session.query(User).all()

        # Update each user's status to active
        for user in users:
            if not user.is_active:
                user.is_active = True
                print(f"Activated User ID {user.id}: {user.email}")

        # Commit the changes to the database
        session.commit()
        print("All users' status updated to active successfully!")

    except Exception as e:
        session.rollback()
        print(f"An error occurred: {e}")

    finally:
        session.close()


if __name__ == "__main__":
    activate_all_users()
