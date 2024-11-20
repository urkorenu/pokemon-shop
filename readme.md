# Pokémon Card Store Web App

A modern web application for managing and showcasing Pokémon cards with advanced search and user-friendly features.

## Features
- Browse Cards: View Pokémon cards with images, names, prices, and other details.
- Advanced Search: Search by Pokémon name, Filter by set name, Sort by price (low to high, high to low) or card number.
- Authentication: User registration and login/logout functionality.
- Admin dashboard for uploading new cards.

## Technologies
- **Backend**: Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login.
- **Database**: PostgreSQL (via Docker).
- **Frontend**: Bootstrap 5.
- **DevOps**: Docker, Kubernetes, ArgoCD, AWS.

## Setup Instructions
1. **Clone Repository**:
    ```bash
    git clone <repository-url>
    cd pokemon-shop
    ```

2. **Set Up Docker**:
    ```bash
    docker-compose up --build
    ```
    Might need to exec and insert this command to initiate the db connection/migration:
    ```bash
    docker-compose exec app flask db init || true  # Initialize migrations
    docker-compose exec app flask db migrate -m "Initial migration" || true  # Create migration scripts
    docker-compose exec app flask db upgrade  # Apply migrations
    ```

3. **Database Migrations**:
    ```bash
    docker-compose exec app flask db upgrade
    ```

4. **Access the App**:
   - Local: [http://localhost:5000](http://localhost:5000)

5. **Deployment**:
   - Deploy via Kubernetes with your preferred CI/CD setup (e.g., ArgoCD).

## Directory Structure
See the main project structure in the documentation.

## Environment Variables
- `SECRET_KEY`: Flask app secret key.
- `DATABASE_URL`: Database connection string.

## To-Do
- Add image upload to S3 for cards.
- Implement pagination for large card collections.
- Improve test coverage with unit and integration tests.

