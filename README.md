# Real-Time Chat API & Web Application

A production-grade, real-time messaging backend and web application built with **Django**, **Django REST Framework (DRF)**, **Django Channels** (WebSockets), and **Tailwind CSS**.

---

## System Architecture

```
                      ┌──────────────┐
                      │    Client    │
                      └──────┬───────┘
                             │
                  ┌──────────┴──────────┐
                  │                     │
                 HTTP               WebSocket
                  │                     │
                  ▼                     ▼
            ┌──────────┐         ┌──────────────┐
            │   DRF    │         │   Channels   │
            └────┬─────┘         └──────┬───────┘
                 │                      │
                 ▼                      ▼
           JWT Authentication      JWT Middleware
                 │                      │
                 │                      ▼
                 │                  Consumer
                 │                      │
                 ▼                      ▼
           ┌──────────────────────────────────┐
           │             Django               │
           │                                  │
           │      User          Message       │
           └────────────────┬─────────────────┘
                            │
                            ▼
                        Database

                      Consumer
                         │
                         ▼
             Redis / InMemory Channel Layer
                         │
                         ▼
                   Channel Groups
```

---

## Tech Stack

| Component | Technology | Description |
|---|---|---|
| **Framework** | Django 4.2+ | Core Web & Admin Framework |
| **REST API** | Django REST Framework | Auth & Chat History Endpoints |
| **Authentication** | Simple JWT | JSON Web Token Access & Refresh Flow |
| **Real-Time** | Django Channels | `AsyncJsonWebsocketConsumer` for WebSockets |
| **Channel Layer** | InMemory / Redis | `InMemoryChannelLayer` (Dev) / `RedisChannelLayer` (Prod) |
| **Database** | SQLite (Dev) | Relational Database with composite index |
| **ASGI Server** | Daphne | Async ASGI Server |
| **Frontend** | Tailwind CSS v4 & Inter | Minimal, modern light white theme web UI |

---

## Project Structure

```
Chat/
├── manage.py                          # Django management script
├── requirements.txt                   # Project dependencies
├── .env.example                       # Environment variables template
├── README.md                          # Project documentation
│
├── config/                            # Root project settings
│   ├── __init__.py
│   ├── settings.py                    # Environment-driven settings & Channel Layers
│   ├── urls.py                        # Root HTTP URL routing (API & Web pages)
│   └── asgi.py                        # ASGI application & WebSocket routing
│
├── apps/                              # Application modules
│   ├── accounts/                      # Authentication & User module
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py             # Registration & User list serializers
│   │   ├── views.py                   # Register & UserList DRF views
│   │   ├── urls.py                    # REST Auth endpoints
│   │   └── tests.py                   # Auth test suite
│   │
│   └── chat/                          # Real-Time Chat module
│       ├── admin.py                   # Message model admin configuration
│       ├── apps.py
│       ├── models.py                  # Message model (sender, receiver, content, timestamp)
│       ├── serializers.py             # Message serializer
│       ├── views.py                   # Message history DRF view
│       ├── urls.py                    # REST Chat endpoints
│       ├── consumers.py               # Async Chat WebSocket consumer
│       ├── routing.py                 # WebSocket URL patterns
│       ├── middleware.py              # Custom JWT WebSocket auth middleware
│       └── tests.py                   # Chat & Channels test suite
│
└── templates/                         # Web Application Templates
    ├── base.html                      # Base layout (Tailwind CSS v4 & Inter font)
    ├── auth/
    │   ├── login.html                 # Modern white-theme Sign In page
    │   └── register.html              # Modern white-theme Sign Up page
    └── chat/
        └── index.html                 # Chat Dashboard (Sidebar + Real-time stream)
```

---

## Setup & Running Locally

### 1. Prerequisites
- **Python 3.10+** installed.

### 2. Installation

```bash
# Clone repository
git clone <repository-url>
cd Chat

# Create & activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Setup & Database Migrations

```bash
# Copy example env file
cp .env.example .env

# Run database migrations
python manage.py migrate
```

### 4. Start Server

```bash
# Start ASGI server using Daphne
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

Open `http://localhost:8000/` in your browser to access the web application!

---

## Web Application Routes

| Route | Description |
|---|---|
| `/` | **Chat Dashboard** — Main chat UI with real-time WebSocket messaging |
| `/login/` | **Sign In Page** — Clean white-themed login screen |
| `/register/` | **Sign Up Page** — Account creation screen |

---

## REST API Reference

### Authentication (`/api/auth/`)

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `POST` | `/api/auth/register/` | No | Register a new user and receive JWT pair |
| `POST` | `/api/auth/login/` | No | Authenticate user and return JWT access/refresh tokens |
| `POST` | `/api/auth/token/refresh/` | No | Refresh an expired access token |
| `GET` | `/api/auth/users/` | Bearer JWT | List all registered users (excluding current user) |

### Chat (`/api/chat/`)

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/api/chat/messages/<user_id>/` | Bearer JWT | Retrieve paginated chat history between current user and target user |

---

## Real-Time WebSocket API

### Chat WebSocket (Direct Messaging)

```
ws://localhost:8000/ws/chat/<target_user_id>/?token=<jwt_access_token>
```

- `target_user_id`: The ID of the recipient user.
- `token`: Valid JWT access token passed via query parameters during handshake.

### Notification WebSocket (Sidebar Updates)

```
ws://localhost:8000/ws/notifications/?token=<jwt_access_token>
```

- Auto-connects on page load to subscribe to the user's personal notification group.
- Receives real-time message events for unread badge updates and sidebar sorting, even before any chat is opened.

### Message Payload Formats

**Client → Server (Send Message):**
```json
{
  "message": "Hello there!"
}
```

**Server → Client (Broadcast Message):**
```json
{
  "type": "chat_message",
  "message": {
    "id": 42,
    "sender": "alice",
    "sender_id": 1,
    "receiver_id": 2,
    "content": "Hello there!",
    "timestamp": "2026-08-18T20:45:00.000000Z"
  }
}
```

---

## How to Test the Project

### Option A: Using the Built-in Web UI (Easiest)
1. Start Daphne: `daphne -b 0.0.0.0 -p 8000 config.asgi:application`
2. Open `http://localhost:8000/register/` to sign up a user.
3. Open a second browser tab (or Incognito) at `http://localhost:8000/register/` to sign up another user.
4. Select a user from the sidebar to test direct real-time messaging!

### Option B: Testing with Postman
1. **REST APIs**:
   - **Login**: `POST http://localhost:8000/api/auth/login/` (JSON: `{"username": "alice", "password": "yourpassword"}`). Copy the `access` token.
   - **User List**: `GET http://localhost:8000/api/auth/users/` (Header: `Authorization: Bearer <access_token>`).
   - **History**: `GET http://localhost:8000/api/chat/messages/2/` (Header: `Authorization: Bearer <access_token>`).
2. **WebSockets in Postman**:
   - In Postman, click **New** → **WebSocket Request**.
   - Set URL: `ws://localhost:8000/ws/chat/2/?token=<access_token>` (replace `2` with recipient user ID).
   - Click **Connect**.
   - In the Message composer, select **JSON** and send:
     ```json
     { "message": "Hello from Postman!" }
     ```
   - Sent and received messages appear live in the Postman connection log!

### Option C: Testing with `wscat`
```bash
npm install -g wscat
wscat -c "ws://localhost:8000/ws/chat/2/?token=<your_access_token>"
> {"message": "Hello via wscat!"}
```

---

## Testing

Run the automated test suite using Django's built-in test runner:

```bash
python manage.py test apps.accounts apps.chat -v 2
```

---

## Key Architecture & Design Decisions

1. **Async WebSocket Consumer (`AsyncJsonWebsocketConsumer`)**:
   - Handles connection lifecycle asynchronously. Uses `database_sync_to_async` for non-blocking ORM operations.

2. **Dual WebSocket Architecture (Chat + Notification)**:
   - `ChatConsumer` (`ws/chat/<user_id>/`) handles direct messaging and joins both the conversation room group and user's personal notification group.
   - `NotificationConsumer` (`ws/notifications/`) is a lightweight consumer that auto-connects on page load, subscribing the user to their personal group (`user_<id>`) so incoming messages trigger sidebar updates immediately — even before any chat is selected.

3. **Deterministic Channel Group Names**:
   - Room names are computed as `chat_{min(id1, id2)}_{max(id1, id2)}`. This guarantees that User A chatting with User B and User B chatting with User A land in the exact same channel group.

4. **Query String JWT Authentication**:
   - Web Browsers cannot send custom HTTP headers during a WebSocket handshake. The custom `JWTAuthMiddleware` parses the `token` query parameter, decodes the JWT, and attaches the authenticated user to the ASGI scope.

5. **Sender Spoofing Protection**:
   - Sender identity is always extracted from the validated JWT scope, never from the WebSocket payload, preventing user impersonation.

6. **Flexible Channel Layer (InMemory vs Redis)**:
   - Configured to use `InMemoryChannelLayer` out of the box for instant local development without external dependencies.
   - Defining `REDIS_URL` in `.env` seamlessly switches to `RedisChannelLayer`.
