# 📦 Logistics Task Marketplace

This repository contains the backend source code for the Logistics Task Marketplace, a platform connecting businesses with runners for task-based logistics. The system is built with FastAPI and PostgreSQL, featuring JWT-based authentication and OTP verification.

## 1. Product Overview

The system is a task-based logistics platform connecting:

-   **Businesses:** Entities that have logistics tasks (deliveries, pickups, errands).
-   **Runners/Users:** Individuals who accept and complete these tasks to earn money.
-   **Admins:** Superusers responsible for managing businesses, tasks, user verification, and payouts.

The platform handles:

-   OTP-based user authentication
-   User identity & profile management
-   Runner verification (ID card + face match)
-   Tasks with multiple steps (multi-stop jobs)
-   Task acceptance & completion
-   A complete wallet & transaction system for earnings
-   Business accounts and admin-driven operations

## 2. Tech Stack

-   **Backend:** FastAPI
-   **Database:** PostgreSQL
-   **Authentication:** JWT (JSON Web Tokens)
-   **OTP Service:** Kavenegar

## 3. Getting Started

### Prerequisites

-   Python 3.8+
-   PostgreSQL
-   Docker (optional, for containerized setup)
-   An account with [Kavenegar](https://kavenegar.com/) for OTP services.

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/logistics-marketplace.git
    cd logistics-marketplace
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## 4. Configuration

The application requires several environment variables to run correctly. Create a `.env` file in the project root and add the following variables:

```
# .env

# PostgreSQL Database
DATABASE_URL=postgresql://user:password@host:port/dbname

# JWT Settings
SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Kavenegar API
KAVENEGAR_API_KEY=your_kavenegar_api_key
```

**Note:** Never commit your `.env` file to version control. Add it to your `.gitignore` file.

## 5. Running the Application

### Without Docker

To run the FastAPI application directly:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### With Docker

A `Dockerfile` is included for easy containerization.

1.  **Build the Docker image:**

    ```bash
    docker build -t logistics-marketplace .
    ```

2.  **Run the Docker container:**

    ```bash
    docker run -d -p 8000:8000 --env-file .env logistics-marketplace
    ```

## 6. API Structure

### Auth Endpoints

-   `POST /auth/send-otp`
-   `POST /auth/verify-otp`

### User Endpoints

-   `GET /me`
-   `PATCH /me`
-   `POST /me/id-card`
-   `POST /me/selfie`

### Admin Endpoints

-   `GET /admin/users`
-   `PATCH /admin/users/{id}/verification`
-   `GET /admin/businesses`
-   `POST /admin/businesses`
-   `PATCH /admin/businesses/{id}`
-   `POST /admin/tasks`
-   `PATCH /admin/tasks/{id}`
-   `GET /admin/tasks`
-   `POST /admin/tasks/{id}/approve`
-   `POST /admin/tasks/{id}/reject`

### Task Endpoints (User)

-   `GET /tasks`
-   `GET /tasks/{id}`
-   `POST /tasks/{id}/accept`
-   `POST /tasks/{id}/complete`
-   `PATCH /tasks/{task_id}/steps/{step_id}`

### Wallet Endpoints

-   `GET /me/wallet`
-   `GET /me/wallet/transactions`

## 7. Deployment

For a production environment, it's recommended to use a more robust setup. A common approach includes:

-   **Web Server:** Nginx or Traefik as a reverse proxy.
-   **Process Manager:** Gunicorn to manage the FastAPI application.
-   **Database:** A managed PostgreSQL service (e.g., AWS RDS, Google Cloud SQL).
-   **Container Orchestration:** Docker Compose or Kubernetes for managing the application and database containers.

### Example with Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  web:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db

  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=dbname

volumes:
  postgres_data:
```

Run with:

```bash
docker-compose up -d
```

## 8. Future Enhancements

-   **Phase 2:** Business login, push notifications, task filtering by distance, geo-tracking, and delivery proof photos.
-   **Phase 3:** Automatic identity verification, runner performance scores, bonus systems, and automatic bank settlements.
