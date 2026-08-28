```mermaid
graph TD
    Client[Client / API Consumer] -->|HTTP Requests| API[Django REST API]

    subgraph "Django Application"
        API --> Auth[Authentication & JWT]
        API --> Users[Users App]
        API --> Events[Events App]
        API --> Enrollments[Enrollments App]

        Auth -->|Signup / Login / Refresh| Users
        Auth -->|Verify JWT| Events
        Auth -->|Verify JWT| Enrollments

        Users -->|Create / Verify OTP| UserDB[(UserProfile, EmailOTP)]
        Users -->|Send email| Email

        Events -->|CRUD + Search| EventDB[(Event)]
        Events -->|My Events| EventDB
        Events -->|Enrollment counts| Enrollments

        Enrollments -->|Enroll / Cancel / List| EnrollmentDB[(Enrollment)]
        Enrollments -->|Lock event row| EventDB
        Enrollments -->|UniqueConstraint| EnrollmentDB

        EventDB -->|Capacity check| Enrollments
    end

    subgraph External
        Email["Email Service (console/file backend)"]
    end
```


┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT (Web / Mobile / Postman)             │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ HTTP / HTTPS (JWT in Authorization header)
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DJANGO REST API (DRF + SimpleJWT)            │
├───────────────────┬───────────────────┬────────────────────────────┤
│   USERS APP       │   EVENTS APP      │   ENROLLMENTS APP          │
│                   │                   │                            │
│ • Signup          │ • CRUD own        │ • Enroll (Challenge A)     │
│ • OTP verify      │   events          │ • Cancel (Challenge B)     │
│ • Resend (C)      │ • Search/filter   │ • Re‑enroll (Challenge B)  │
│ • Login           │ • Pagination      │ • My enrollments           │
│ • JWT tokens      │ • Permissions     │ • Concurrency protection   │
└───────────────────┴───────────────────┴────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                DATABASE (PostgreSQL / SQLite)                       │
│  • UserProfile (role, email_verified)                               │
│  • EmailOTP (hashed, expires, attempts, last_sent)                  │
│  • Event (title, description, location, starts/ends, capacity)      │
│  • Enrollment (event, seeker, status)                               │
│    → UniqueConstraint: (event, seeker) WHERE status='enrolled'      │
└─────────────────────────────────────────────────────────────────────┘


## Setup & Installation

# Clone the repository
git clone <repository-url>
cd events_platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Run migrations
python manage.py migrate

# Create a superuser (optional)
python manage.py createsuperuser

# Start the server
python manage.py runserver



## Core API Endpoints

| Resource | Method | Endpoint | Allowed Roles |
|---|---|---|---|
| Signup | `POST` | `/api/users/signup/` | Public |
| Verify OTP | `POST` | `/api/users/verify-email/` | Public |
| Resend OTP | `POST` | `/api/users/resend-otp/` | Public |
| Login | `POST` | `/api/users/login/` | Public |
| Refresh Token | `POST` | `/api/token/refresh/` | Public |
| List Events | `GET` | `/api/events/` | Public |
| Create Event | `POST` | `/api/events/` | Facilitator only |
| Retrieve Event | `GET` | `/api/events/{id}/` | Public |
| Update Event | `PUT/PATCH` | `/api/events/{id}/` | Facilitator (Owner) |
| Delete Event | `DELETE` | `/api/events/{id}/` | Facilitator (Owner) |
| My Events | `GET` | `/api/events/my-events/` | Facilitator |
| Enroll | `POST` | `/api/enrollments/` | Seeker only |
| Cancel Enrollment | `DELETE` | `/api/enrollments/{id}/cancel/` | Seeker (Owner) |
| My Enrollments | `GET` | `/api/enrollments/my-enrollments/` | Seeker |


🚀 What I Would Improve With More Time
1) Full-Text Search — Use PostgreSQL SearchVector for faster and more relevant event discovery.
2) Redis Integration — Add caching for frequently accessed event listings and implement distributed rate limiting.
3) Production Email Delivery — Replace the development email backend with a provider such as SendGrid or AWS SES.
4) Real-Time Updates — Add WebSocket support for real-time event capacity and enrollment updates.
5) API Documentation — Add comprehensive Swagger/OpenAPI documentation for all endpoints.
6) Consistent Error Handling — Standardize validation and application errors across all API endpoints.
7) Production Docker Setup — Add Gunicorn, Nginx, SSL, and production-ready Docker configuration.
8) CI/CD Pipeline — Automate testing, linting, and deployment through a CI/CD pipeline.
9) Seed Data — Add fixtures or management commands to simplify local setup and demonstrations.


## Mandatory Documentation Files

| File | Content |
|---|---|
| `PROMPT_LOG.md` | AI prompts, tools/models used, what was used/changed/rejected, and at least 2 examples of AI-generated suggestions that were incorrect and corrected. |
| `DECISIONS.md` | At least 3 non-trivial engineering decisions, including the ambiguity, options considered, chosen approach, and trade-offs. |
| `DEBUGGING.md` | At least 2 real issues or failed assumptions, including the symptom, diagnosis, root cause, fix, and verification. |
| `README.md` | Project setup and run instructions, architecture overview, known limitations, and potential improvements. |