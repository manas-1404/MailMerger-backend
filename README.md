# MailMerger Backend

MailMerger-backend is a robust and scalable backend API designed for managing personalized email campaigns with advanced features like template management, email queueing, and user authentication. Built with FastAPI, SQLAlchemy, and Redis, it supports efficient email processing and template storage for high-performance applications.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [Configuration](#configuration)
- [API Overview](#api-overview)
  - [Authentication & User](#authentication--user)
  - [Email Queue](#email-queue)
  - [Templates](#templates)
  - [Storage](#storage)
- [Background Tasks](#background-tasks)
- [Development & Testing](#development--testing)
- [Contribution](#contribution)
- [License](#license)

---

## Features

- **User Authentication:** JWT-based login, signup, and refresh tokens. OAuth support (Google).
- **Email Queue:** Queue emails for asynchronous sending, retrieve or delete queued emails.
- **Template Management:** Create, manage, and cache email templates per user.
- **Storage Integration:** Connects to Supabase S3 for file storage needs.
- **Database:** Uses SQLAlchemy ORM with PostgreSQL (configurable).
- **Caching:** Heavy use of Redis for caching templates and email queues for fast access.
- **Background Processing:** Celery tasks for sending emails in the background.
- **Configurable CORS:** Supports cross-origin requests from configurable origins.

---

## Tech Stack

- **Framework:** FastAPI (Python)
- **ORM:** SQLAlchemy
- **Database:** PostgreSQL (via `DB_CONNECTION_URL`)
- **Cache:** Redis (local/cloud, configurable)
- **Task Queue:** Celery (for background email sending through redis queue)
- **Storage:** Supabase S3
- **Auth:** JWT, OAuth (Google)

---

## Project Structure

```
app/
  ├── main.py              # FastAPI app entry point, middleware & router registration
  ├── models/              # SQLAlchemy models (User, Email, Template, etc.)
  ├── routes/              # API route definitions (auth, email, template, queue, storage)
  ├── utils/               # Utility functions & configuration
  ├── db/                  # Database & Redis connection setup
  ├── pydantic_schemas/    # Request/response validation schemas
  └── tasks/               # Celery tasks for background jobs
```

---

## Setup and Installation

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Redis server (local or cloud)
- Supabase account (for S3 storage)
- [Optional] Celery worker (for background email sending)

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/manas-1404/MailMerger-backend.git
   cd MailMerger-backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   - Copy `.env.example` to `.env` and fill in all required values (see [Configuration](#configuration) below).

4. **Run database migrations:**
   > Tables are auto-created at FastAPI startup, but for production, set up migrations via Alembic if needed.

5. **Start the FastAPI server:**
   ```bash
   uvicorn app.main:app --reload --host localhost --port 8000
   ```

6. **[Optional only if sending batched emails] Start Celery worker:**
   ```bash
   celery -A app.celery_worker worker --loglevel=info --pool=solo
   ```

---

## Configuration

All critical settings are controlled via environment variables (see `app/utils/config.py`):

- `DB_CONNECTION_URL` - PostgreSQL connection string
- `REDIS_HOST`, `REDIS_SERVER_PORT`, `REDIS_SERVER_DB` - Redis config (local)
- `REDIS_CLOUD_*` - Redis config (cloud)
- `SUPABASE_ACCESS_KEY_ID`, `SUPABASE_SERVICE_ROLE` - Supabase credentials
- `SUPABASE_S3_STORAGE_ENDPOINT`, `SUPABASE_S3_STORAGE_REGION` - Supabase S3 config
- `JWT_SIGNATURE_SECRET_KEY`, `JWT_AUTH_ALGORITHM` - JWT auth secrets
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` - Google OAuth credentials
- `ALLOWED_ORIGINS` - CORS allowed origins

See `app/utils/config.py` for the full list.

---

## API Overview

### Authentication & User

- **Endpoints:**
  - `POST /api/auth/login` - Login and receive JWT token
  - `POST /api/auth/signup` - Register new users
- **Details:**
  - Credentials verified against hashed passwords.
  - On login, user's templates are cached in Redis for faster access.
  - JWT and refresh tokens are set as cookies.

### Email Queue

- **Endpoints:**
  - `GET /api/queue/get-email-queue` - Retrieve queued emails for the user
  - `POST /api/queue/add-to-queue` - Add an email to the queue
  - `POST /api/queue/send-queued-emails` - Send queued emails (processed via Celery)
  - `DELETE /api/queue/delete-queue-email` - Remove emails from the queue
- **Details:**
  - Queues are stored in Redis for performance, fallback to DB if not cached.
  - Email sending is performed asynchronously via Celery background worker.

### Templates

- **Endpoints:**
  - `GET /api/templates/get-all-templates` - Fetch all templates for authenticated user
  - `POST /api/templates/add-template` - Add a new template
  - Other CRUD template endpoints available.
- **Details:**
  - Templates are cached in Redis for each user to minimize DB queries.
  - All cache operations have expiry set for performance and consistency.

### Storage

- **Endpoints:**
  - Storage endpoints connect to Supabase S3; see `app/routes/storage_routes.py` for details.

---

## Background Tasks

- **Celery** is used for sending emails in the background.
- When a user requests to send queued emails, `send_emails_from_user_queue` Celery task is triggered.
- Ensure that the Celery worker is running and configured to connect to the same Redis instance as the server.

---

## Development & Testing

- **Run locally:** Follow setup instructions above.
- **Testing:** Add tests in a `tests/` directory and use `pytest` for running them.
- **Hot reload:** Use `uvicorn ... --reload` for auto-reloading during development.

---

## Contribution

Contributions are welcome! Please open issues or submit pull requests with improvements or bug fixes.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
