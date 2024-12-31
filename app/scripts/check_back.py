from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models import Card
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

def check_back_images():
    try:
        # Query all cards
        cards = session.query(Card).all()

        # Check for back_image_url presence and print results
        for card in cards:
            has_back_image = bool(card.back_image_url)  # True if back_image_url is not None or empty
            print(f"Card ID {card.id}: {card.name}")
            print(f"  Front Image URL: {card.image_url}")
            if has_back_image:
                print(f"  Back Image URL: {card.back_image_url}")
            else:
                print("  Back Image URL: MISSING")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        session.close()

if __name__ == "__main__":
    check_back_images()

