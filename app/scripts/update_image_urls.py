from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models import Card
import re
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

def update_card_image_urls():
    try:
        # Query all cards
        cards = session.query(Card).all()

        # Define the old and new S3 URL patterns
        old_base_url = "https://pokemon-pics.s3.eu-north-1.amazonaws.com/"
        new_base_url = "https://pokemon--pics.s3.il-central-1.amazonaws.com/"

        # Update the image_url for each card
        for card in cards:
            if card.image_url and card.image_url.startswith(old_base_url):
                # Replace the old URL base with the new one
                updated_url = re.sub(r"^https://pokemon-pics.s3.eu-north-1.amazonaws.com/",
                                     new_base_url,
                                     card.image_url)
                card.image_url = updated_url
                print(f"Updated Card ID {card.id}: {updated_url}")

        # Commit the changes to the database
        session.commit()
        print("All image URLs updated successfully!")

    except Exception as e:
        session.rollback()
        print(f"An error occurred: {e}")

    finally:
        session.close()

if __name__ == "__main__":
    update_card_image_urls()
