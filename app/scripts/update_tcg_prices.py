from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models import Card
from config import Config
import requests
import os
from flask import Flask, request
from app.routes.seller_routes import get_card_details

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
app = Flask(__name__)
app.app_context().push()

def fetch_tcg_price(card_name, set_name, number, card_type):
    """Fetch the latest price for a card using the get_card_details function."""
    with app.test_request_context(
            f"/card-details?language=en&set_name={set_name}&number={number}"
    ):
        response = get_card_details()

    if response.status_code != 200:
        print(f"Error fetching TCG price for {card_name}: {response.json.get('error', 'Unknown error')}")
        return None

    data = response.get_json()
    prices = data.get("prices", {})
    market_price = prices.get(card_type.lower(), {}).get("market")

    if market_price is None:
        print(f"No market price found for card '{card_name}' with type '{card_type}'")

    return market_price


def analyze_price_changes(cards, price_changes):
    """Analyze and print the top 10 price increases and decreases."""
    sorted_changes = sorted(price_changes, key=lambda x: x[1], reverse=True)
    print("\nTop 10 Price Increases:")
    for card, change in sorted_changes[:10]:
        print(f"{card.name} (Set: {card.set_name}, Number: {card.number}) - Change: +{change:.2f}")

    print("\nTop 10 Price Decreases:")
    for card, change in sorted_changes[-10:]:
        print(f"{card.name} (Set: {card.set_name}, Number: {card.number}) - Change: {change:.2f}")


def update_tcg_prices():
    try:
        print("Starting TCG price update process...")

        # Query all cards with follow_tcg=True and amount == 1
        cards = session.query(Card).filter(Card.follow_tcg == True, Card.amount == 1).all()
        total_old_price = 0
        total_new_price = 0
        price_changes = []

        if not cards:
            print("No cards found with follow_tcg=True.")
            return

        for card in cards:
            card_id = card.id
            card_name = card.name
            set_name = card.set_name
            number = card.number
            card_type = card.card_type

            print(f"Fetching TCG price for card: {card_name} (Set: {set_name}, Number: {number})")
            new_price = fetch_tcg_price(card_name, set_name, number, card_type)
            if new_price is not None:
                total_old_price += card.price
                old_price = card.price
                card.tcg_price = new_price
                card.price = round(new_price * 3.56 + 0.5, 0)
                card.price = max(card.price, 1)
                total_new_price += card.price
                price_changes.append((card, card.price - old_price))
                print(f"Updated card '{card_name}' with new TCG price: {new_price}")
            else:
                print(f"No price found for card '{card_name}'")

        # Commit changes to the database
        session.commit()
        print("\nTCG price update process completed successfully!")
        print(f"Total old price: {total_old_price}")
        print(f"Total new price: {total_new_price}")
        print(f"Total price difference: {total_new_price - total_old_price}")

        # Perform analysis
        analyze_price_changes(cards, price_changes)

    except Exception as e:
        session.rollback()
        print(f"An error occurred: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    update_tcg_prices()
