from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models import Card
from config import Config
import requests
import os

# Database configuration
DATABASE_URI = (
    f"postgresql+psycopg2://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)
BASE_URL = "https://api.pokemontcg.io/v2"
API_KEY = Config.API_KEY


# Create a database engine
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()


def fetch_tcg_price(card_name, set_name, number, card_type):
    """Fetch the latest price for a card from TCGPlayer."""
    try:
        # Construct the query
        query = f'set.name:"{set_name}" number:"{number}"'
        response = requests.get(
            f"{BASE_URL}/cards",
            headers={"X-Api-Key": API_KEY},
            params={"q": query},
            timeout=10,
        )
        response.raise_for_status()

        # Parse the API response
        card_data = response.json().get("data", [])
        if not card_data:
            print(f"No card found for query: {query}")
            return None

        # Filter for an exact match
        filtered_cards = [
            card
            for card in card_data
            if card.get("set", {}).get("name", "").strip().lower()
            == set_name.strip().lower()
            and str(card.get("number", "")).strip().lower()
            == str(number).strip().lower()
        ]

        if not filtered_cards:
            print(f"No exact match found for query: {query}")
            return None

        # Extract the card details
        card_details = filtered_cards[0]
        tcg_price_data = card_details.get("tcgplayer", {}).get("prices", {})

        # Fetch the price based on card_type
        market_price = tcg_price_data.get(card_type.lower(), {}).get("market")

        if market_price is None:
            print(
                f"No market price found for card '{card_name}' with type '{card_type}'. Full API Response: {response.json()}"
            )

        print(f"Fetched price for card '{card_name}' ({card_type}): {market_price}")
        return market_price
    except requests.RequestException as e:
        print(f"Error fetching TCG price for {card_name}: {e}")
        return None


def update_tcg_prices():
    try:
        print("Starting TCG price update process...")

        # Query all cards with follow_tcg=True and amount == 1
        cards = (
            session.query(Card).filter(Card.follow_tcg == True, Card.amount == 1).all()
        )
        total_old_price = 0
        total_new_price = 0

        if not cards:
            print("No cards found with follow_tcg=True.")
            return

        for card in cards:
            card_id = card.id
            card_name = card.name
            set_name = card.set_name
            number = card.number

            print(
                f"Fetching TCG price for card: {card_name} (Set: {set_name}, Number: {number})"
            )
            # Fetch the updated price
            new_price = fetch_tcg_price(card_name, set_name, number, card.card_type)
            if new_price is not None:
                total_old_price += card.price
                # Update the database
                card.tcg_price = new_price
                card.price = round(new_price * 3.56 + 0.5, 0)
                card.price = 1 if card.price < 1 else card.price
                total_new_price += card.price
                print(f"Updated card '{card_name}' with new TCG price: {new_price}")
            else:
                print(f"No price found for card '{card_name}'")

        # Commit changes to the database
        session.commit()
        print("TCG price update process completed successfully!")
        print(f"Total old price: {total_old_price}")
        print(f"Total new price: {total_new_price}")
        print(f"Total price difference: {total_new_price - total_old_price}")

    except Exception as e:
        session.rollback()
        print(f"An error occurred: {e}")

    finally:
        session.close()


if __name__ == "__main__":
    update_tcg_prices()
