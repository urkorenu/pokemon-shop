from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models import Card
from config import Config
import requests
import os
from flask import Flask, request
import urllib.parse
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
    """Fetch the latest price for a card using the cached route."""
    try:
        # Encode the set name and number
        encoded_set_name = urllib.parse.quote(set_name.strip())
        encoded_number = urllib.parse.quote(number.strip())
        normalized_card_type = card_type.lower()

        # Construct the URL for the card details API
        api_url = f"http://localhost:5000/seller/card-details?language=en&set_name={encoded_set_name}&number={encoded_number}"
        headers = {"X-Bypass-Token": os.getenv("BYPASS_TOKEN")}
        response = requests.get(api_url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(
                f"Error fetching TCG price for {card_name}: {response.json().get('error', 'Unknown error')}"
            )
            print(
                f"API error for {card_name}:API URL: {api_url}, {response.status_code} - {response.text}"
            )
            return None

        # Parse the response
        data = response.json()
        prices = data.get("prices", {})
        market_price = None
        for key, value in prices.items():
            if key.lower() == normalized_card_type:
                market_price = value.get("market")
                break
        if market_price is None:
            print(
                f"No market price for {card_name}. Prices: {prices}. card type: {card_type}"
            )

        return market_price
    except requests.RequestException as e:
        print(f"Error fetching TCG price for {card_name}: {e}")
        return None


def analyze_price_changes(cards, price_changes):
    """Analyze and print the top 10 price increases and decreases."""
    sorted_changes = sorted(price_changes, key=lambda x: x[1], reverse=True)
    print("\nTop 10 Price Increases:")
    for card, change in sorted_changes[:10]:
        print(
            f"{card.name} (Set: {card.set_name}, Number: {card.number}) - Change: +{change:.2f}"
        )

    print("\nTop 10 Price Decreases:")
    for card, change in sorted_changes[-10:]:
        print(
            f"{card.name} (Set: {card.set_name}, Number: {card.number}) - Change: {change:.2f}"
        )


def update_tcg_prices():
    try:
        print("Starting TCG price update process...")

        # Query all cards with follow_tcg=True and amount == 1
        cards = (
            session.query(Card)
            .filter(~Card.card_type.ilike("jpn"), Card.amount == 1)
            .all()
        )
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

            new_price = fetch_tcg_price(card_name, set_name, number, card_type)
            if new_price is not None:
                old_price = card.price
                old_tcg_price = card.tcg_price
                card.tcg_price = new_price
                new_price_ils = max(round(new_price * 3.65 + 0.5, 0), 1)
                if card.follow_tcg:
                    card.price = new_price_ils
                else:
                    old_price = max(round(old_tcg_price * 3.65 + 0.5, 0), 1)
                total_old_price += old_price
                total_new_price += new_price_ils
                price_changes.append((card, new_price_ils - old_price))
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
