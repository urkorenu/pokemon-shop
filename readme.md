# Pokémon Card Store Web App

## Features
- Display Pokémon cards with images and details.
- Search, sort, add to cart, and order functionality for users.
- Admin dashboard for uploading new cards.

## Technologies
- **Backend**: Flask, Flask-SQLAlchemy, Flask-Migrate.
- **Database**: PostgreSQL (via Docker).
- **DevOps**: Docker, Kubernetes, ArgoCD, AWS.

## Setup Instructions
1. **Clone Repository**:
    ```bash
    git clone <repository-url>
    cd pokemon-card-store
    ```

2. **Set Up Docker**:
    ```bash
    docker-compose up --build
    ```
    might need to exec and insert this command to initiate the db connection/migration:
    ```bash
    flask db init || true  # Initialize migrations (ignore if already exists)
    flask db migrate -m "Initial migration" || true  # Create migration scripts
    flask db upgrade  # Apply Migrations
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
- Add CI/CD with GitHub Actions and ArgoCD.
- Set up S3 for storing card images.
- Implement a user authentication system.

