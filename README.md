# Ping CRM

An AI-powered personal networking CRM that helps you maintain professional relationships. Import your contacts, connect your email and messaging accounts, and get intelligent follow-up suggestions with AI-drafted messages.

**One-line pitch:** Upload your contacts, connect your accounts. Ping tells you who to reach out to and writes the message.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Setup Guide](#setup-guide)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Database Setup](#2-database-setup-postgresql)
  - [3. Redis Setup](#3-redis-setup)
  - [4. Backend Setup](#4-backend-setup)
  - [5. Frontend Setup](#5-frontend-setup)
  - [6. Platform Credentials](#6-platform-credentials)
  - [7. Running the Application](#7-running-the-application)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Celery Beat Schedule](#celery-beat-schedule)
- [Testing](#testing)

---

## Features

### Dashboard (`/dashboard`)

The main screen provides a real-time overview of your networking activity:

- **Total Contacts** -- count of all contacts in your CRM
- **Pending Suggestions** -- follow-up suggestions awaiting your action
- **Identity Matches** -- potential duplicate contacts detected across platforms
- **Reach Out This Week** -- top 3 contacts recommended for follow-up, with reasons and AI-drafted messages
- **Recent Activity** -- contacts you've interacted with recently
- **Relationship Health** -- breakdown of contacts by status (active, warming, going cold)

### Contact Management

#### Contact List (`/contacts`)

- Paginated, sortable contact list with search
- **Full-text search** across contact names, emails, companies, Twitter handles, Telegram usernames, Twitter bios, Telegram bios, and interaction message content
- Sort by name, relationship score, or last interaction date
- Filter by tags
- Relationship strength color indicators (green/yellow/red)
- Avatar display with fallback initials
- **Bulk actions** -- multi-select contacts to add/remove tags, set priority level, set company, archive, merge, or delete

#### Contact Detail (`/contacts/[id]`)

- **Inline editing** -- click any field to edit directly (name, email, company, title, phone, tags, notes, Twitter handle, Telegram username, LinkedIn URL)
- **Company autocomplete** -- when editing the Company field, search existing organizations with a dropdown. Select an org to link the contact, or type a new name
- **Quick message composer** -- always-visible collapsed bar above the timeline. Click to expand into a full message editor with channel selection (email, Telegram, Twitter)
- **Interaction timeline** -- chronological feed of all touchpoints across email, Telegram, Twitter, and manual notes, with platform icons and direction indicators. Bio changes appear as event pills in the timeline.
- **Add manual notes** -- record offline conversations or meetings
- **Telegram common groups** -- sidebar card showing shared Telegram groups with a contact (cached for 24 hours)
- **Rate limit handling** -- Telegram send shows countdown timer on 429 with Retry-After header
- **Duplicate detection** -- find and merge potential duplicate contacts
- **Relationship score badge** -- color-coded score with label (Active, Warm, Cooling, At Risk)
- **Edit and delete notes** -- hover pencil/trash icons on manual notes in the timeline
- **Auto-sync on visit** -- Telegram and Twitter messages sync automatically when viewing a contact
- **Auto-dismiss suggestions** -- pending follow-up suggestions dismissed when new interactions are synced
- **Delete contact** with confirmation dialog

#### Import Methods

- **CSV upload** -- drag-and-drop or file picker. Supports columns: `name`, `email`, `twitter`, `telegram`, `company`, `notes`
- **Google Contacts sync** -- one-click OAuth import of name, email, phone, company, and title
- **Manual entry** -- add contacts one at a time through the UI (`/contacts/new`)

### Platform Integrations

#### Gmail (`Settings > Gmail`)

- OAuth 2.0 connection with Google
- Multi-account support -- connect multiple Google accounts
- **Email sync** -- imports email threads as interactions (sender, recipient, subject, timestamps, body snippets)
- **Google Contacts sync** -- one-way import of contacts from your Google address book
- **Google Calendar sync** -- imports calendar events as meeting interactions
- All syncs run as background Celery tasks with notification on completion or failure

#### Telegram (`Settings > Telegram`)

- MTProto client integration (accesses your actual chat history, not bot API)
- Phone number + OTP verification flow
- Two-step verification (2FA) support for accounts with cloud passwords
- **Chat sync** -- imports DM conversations as interactions (skips unchanged dialogs to reduce API calls)
- **Group member sync** -- discovers contacts from shared Telegram groups
- **Bio sync** -- captures Telegram bios for your contacts (7-day freshness filter to reduce API calls)
- **Common groups** -- view which Telegram groups you share with a specific contact
- **Rate gate** -- Redis-based cross-operation coordination prevents FloodWaitError cascades
- Background sync with progress notifications

#### Twitter/X (`Settings > Twitter`)

- OAuth 2.0 PKCE authentication flow
- **Bird CLI** (`@steipete/bird`) -- cookie-based tweet/profile fetching bypassing API rate limits, with Twitter API as fallback
- **DM sync** -- imports direct message conversations using per-conversation API (`/dm_conversations/with/:id`)
- **Mention sync** -- tracks @mentions and replies
- **Bio monitoring** -- detects bio changes (job changes, milestones), stores them as events, and adds them to the contact timeline
- Background sync with retry logic and failure notifications

#### LinkedIn (`Chrome Extension`)

- Companion Chrome extension (`chrome-extension/`) for passive LinkedIn data capture
- **Profile sync** -- captures name, headline, company, location, avatar when visiting profiles
- **Message sync** -- captures DM conversations from full-page messaging and overlay chat
- **Avatar download** -- high-res profile photos saved locally with SSRF domain allowlist
- Content-hash deduplication prevents duplicate messages
- Settings persist across browser sessions via chrome.storage.local

### Identity Resolution (`/identity`)

Automatically detects when contacts across different platforms are the same person:

- **Tier 1: Deterministic matching** (auto-merge) -- same email, same phone number, email found in Twitter bio
- **Tier 2: Probabilistic matching** (scored) -- weighted formula:
  - Email domain match: 40%
  - Name similarity: 20%
  - Company match: 20%
  - Username similarity: 10%
  - Mutual signals: 10%
  - Auto-merges above 85% confidence
  - Colleague guard: caps score when names differ but company/email domain match (prevents false positives for coworkers)
- **Tier 4: Manual review** -- side-by-side comparison cards for low-confidence matches
- **Merge or reject** -- one-click actions to combine duplicate profiles or dismiss false matches
- **Scan button** -- trigger identity resolution on demand

### Organizations (`/organizations`)

Manage companies and organizations your contacts belong to:

#### Organization List (`/organizations`)

- Flat table with sortable column headers (name, contacts, avg score, interactions, last activity)
- Click any column header to sort; active sort shows arrow indicator
- **Domain favicon** -- automatically fetches favicon from the org's domain as a logo
- **Search** -- filter organizations by name
- **Select and merge** -- checkbox selection with bulk merge for duplicate organizations
- **Per-row delete** -- trash icon on each row with confirmation dialog
- **Bulk actions bar** -- appears on selection with merge and delete options
- Pagination for large datasets

#### Organization Detail (`/organizations/[id]`)

- **Inline editing** -- hover any field to reveal pencil icon, click to edit in place (name, location, website, LinkedIn, Twitter, notes)
- **Stats cards** -- contacts count, avg relationship score, total interactions, last activity (from materialized view, refreshed hourly)
- **Contacts table** -- sortable list of active contacts in the organization with score badges
- **Auto-hidden** -- organizations with zero active (non-archived) contacts are hidden from the list
- **Delete organization** -- unlinks contacts but does not delete them

### Smart Follow-Up Suggestions (`/suggestions`)

AI-generated recommendations for who to reach out to and why:

- **Time-based triggers** -- no interaction in 90+ days, declining relationship score
- **Event-based triggers** -- detected job changes, fundraising announcements, product launches from Twitter activity
- **Scheduled triggers** -- user-set manual reminders with snooze reactivation
- **AI message composer** -- generates contextual draft messages using Claude 3.5 Haiku, considering:
  - Contact profile (name, company, role)
  - Last interaction summary and when it occurred
  - Detected events (the reason for reaching out now)
  - Conversation tone (formal vs. casual, based on past messages)
  - Preferred channel (email, Telegram, Twitter)
- **Actions per suggestion:**
  - Edit the AI-drafted message and mark as sent
  - Snooze (2 weeks / 1 month / 3 months)
  - Dismiss entirely
- **Generate new suggestions** on demand with one click

### Relationship Scoring

Automatic scoring of relationship health based on interaction patterns:

| Signal | Points |
|--------|--------|
| Message exchanged in last 30 days | +5 |
| Reply within 48 hours | +3 |
| Introduction or referral made | +2 |
| Mutual interaction (both sides initiate) | +2 |
| Per month of silence | -2 |

Score interpretation:

- **8+** (Green) -- Active relationship, no follow-up needed
- **4-7** (Yellow) -- Warm, could use a check-in soon
- **1-3** (Orange) -- Cooling off, follow-up recommended
- **0 or below** (Red) -- At risk of going cold

### Context Detection Engine

Monitors Twitter activity from contacts and classifies events worth acting on:

| Event | Signal Source | Example |
|-------|-------------|---------|
| Job change | Twitter bio update, tweet | "Excited to join Stripe" |
| Fundraising | Tweet, email mention | "We just closed our seed round" |
| Product launch | Tweet | "We shipped today" |
| Promotion | Twitter bio | New title in bio |
| Personal milestone | Tweet | Wedding, move, new baby |
| Conference/event | Tweet, email | Speaking at or attending an event |

Uses Claude for LLM-powered event classification with confidence scoring.

### Notifications (`/notifications`)

In-app notification center for all system events:

- Sync completion and failure alerts
- New follow-up suggestion notifications
- Bio change detections
- Identity match discoveries
- Mark individual or all notifications as read
- Click any notification to navigate to the relevant page
- Unread badge in navigation

### Settings (`/settings`)

Central hub for managing all platform connections and data sync:

- **Gmail** -- connect/disconnect, view connected email, sync contacts, sync calendar events
- **Telegram** -- connect via phone number, OTP verification, 2FA support, sync chats
- **Twitter** -- OAuth connect/disconnect, sync DMs and mentions
- **CSV Import** -- upload contact spreadsheets with drag-and-drop
- Connection status badges showing connected accounts and usernames

### Onboarding (`/onboarding`)

Guided 4-step setup flow for new users:

1. Welcome screen
2. Connect Google account
3. Import contacts
4. Done -- redirects to dashboard

### Authentication

- **Google OAuth** -- sign in with Google account
- **Email/password** -- register and login with email
- JWT-based session management (24-hour token expiry)
- Protected routes with automatic redirect to login

### Error Handling

- Global error boundary with recovery action
- 404 Not Found page
- Per-page error states with retry buttons
- Empty states with helpful guidance for new users

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.12 + FastAPI |
| **Database** | PostgreSQL (via SQLAlchemy 2.x async + asyncpg) |
| **Migrations** | Alembic |
| **Task Queue** | Redis + Celery |
| **AI** | Anthropic Claude 3.5 Haiku (event classification + message composition) |
| **Frontend** | Next.js 15 + React 19 + Tailwind CSS v4 |
| **State Management** | TanStack React Query v5 |
| **Telegram** | Telethon (MTProto client) |
| **Google APIs** | google-api-python-client + google-auth-oauthlib |
| **Auth** | python-jose (JWT) + passlib (bcrypt) |
| **HTTP Client** | httpx (async) + openapi-fetch (frontend) |
| **Testing** | pytest (backend, 631 tests) + Vitest (frontend, 481 tests) |

---

## Prerequisites

- **Python 3.12+**
- **Node.js 18+** and npm
- **PostgreSQL 14+**
- **Redis 6+**

---

## Setup Guide

### 1. Clone the Repository

```bash
git clone https://github.com/sneg55/pingcrm.git
cd pingcrm
```

### 2. Database Setup (PostgreSQL)

Create the database:

```bash
createdb pingcrm
```

Or via psql:

```sql
CREATE DATABASE pingcrm;
```

### 3. Redis Setup

Install and start Redis:

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis
```

Verify Redis is running:

```bash
redis-cli ping
# Should return: PONG
```

### 4. Backend Setup

```bash
cd backend

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

Edit `.env` with your credentials (see [Environment Variables](#environment-variables) for the full list):

```env
# REQUIRED: Generate a secure secret key
SECRET_KEY=<run: python -c "import secrets; print(secrets.token_urlsafe(64))">

# Database
DATABASE_URL=postgresql+asyncpg://localhost:5432/pingcrm

# Redis
REDIS_URL=redis://localhost:6379/0
```

Run database migrations:

```bash
alembic upgrade head
```

### 5. Frontend Setup

```bash
cd frontend
npm install
```

No additional frontend configuration is needed for local development. The frontend proxies all `/api/*` requests to the backend via Next.js rewrites (default: `http://localhost:8000`, configurable via `NEXT_PUBLIC_API_URL`).

### 6. Platform Credentials

All platform integrations are optional. The app works without them -- you can add contacts manually or via CSV and connect platforms later.

#### Google OAuth (login + Gmail + Contacts + Calendar)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or select existing)
3. Enable these APIs:
   - Gmail API
   - Google People API (for contacts)
   - Google Calendar API
4. Go to **Credentials > Create Credentials > OAuth 2.0 Client ID**
5. Set application type to **Web application**
6. Add authorized redirect URI: `http://localhost:3000/auth/google/callback`
7. Copy Client ID and Client Secret to `.env`:
   ```env
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret
   ```

#### Twitter/X API (DMs, mentions, bio monitoring)

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a project and app
3. Enable **OAuth 2.0** with PKCE
4. Set callback URL: `http://localhost:3000/auth/twitter/callback`
5. Request access to scopes: `dm.read`, `tweet.read`, `users.read`, `offline.access`
6. Copy credentials to `.env`:
   ```env
   TWITTER_CLIENT_ID=your_client_id
   TWITTER_CLIENT_SECRET=your_client_secret
   TWITTER_API_KEY=your_api_key
   TWITTER_API_SECRET=your_api_secret
   TWITTER_REDIRECT_URI=http://localhost:3000/auth/twitter/callback
   ```

#### Telegram (chat sync, group discovery)

1. Go to [my.telegram.org](https://my.telegram.org/)
2. Log in with your phone number
3. Go to **API development tools**
4. Create a new application
5. Copy credentials to `.env`:
   ```env
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   ```

#### Anthropic / Claude AI (message generation, event classification)

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create an API key
3. Add to `.env`:
   ```env
   ANTHROPIC_API_KEY=your_api_key
   ```

### 7. Running the Application

You need **3-4 terminal windows** for full functionality:

**Terminal 1 -- Backend API:**
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
# Runs on http://localhost:8000
```

**Terminal 2 -- Frontend:**
```bash
cd frontend
npm run dev
# Runs on http://localhost:3000
```

**Terminal 3 -- Celery Worker + Beat (development, single process):**
```bash
cd backend
source .venv/bin/activate
celery -A worker.celery_app worker --beat --loglevel=info
```

Or as separate processes (recommended for production):

```bash
# Terminal 3 -- Celery Beat (scheduler)
celery -A worker.celery_app beat --loglevel=info

# Terminal 4 -- Celery Worker
celery -A worker.celery_app worker --loglevel=info
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Docker Setup (Alternative)

```bash
# Set required env vars
export POSTGRES_PASSWORD=your_password
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))")

# Start all services
docker compose up

# Run migrations
docker compose exec backend alembic upgrade head
```

For production, use `docker-compose.prod.yml` which adds Caddy reverse proxy with automatic HTTPS.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | **Yes** | JWT signing key. Generate with: `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `DATABASE_URL` | **Yes** | PostgreSQL connection string (asyncpg format) |
| `REDIS_URL` | No | Redis URL for Celery (default: `redis://localhost:6379/0`) |
| `ALGORITHM` | No | JWT signing algorithm (default: `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | JWT token lifetime in minutes (default: `1440`, i.e. 24 hours) |
| `ENCRYPTION_KEY` | No | Fernet key for encrypting stored OAuth tokens. Generate with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `CORS_ORIGINS` | No | JSON array of allowed CORS origins (default: `["http://localhost:3000","http://127.0.0.1:3000"]`) |
| `AUTH_TOKEN` | No | `auth_token` cookie from x.com for Bird CLI |
| `CT0` | No | `ct0` CSRF cookie from x.com for Bird CLI |
| `CHROME_EXTENSION_ID` | No | Chrome extension ID for CORS (auto-detected in dev) |
| `GOOGLE_CLIENT_ID` | No | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | No | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | No | Google OAuth callback URL (default: `http://localhost:3000/auth/google/callback`) |
| `TWITTER_API_KEY` | No | Twitter API v2 key |
| `TWITTER_API_SECRET` | No | Twitter API v2 secret |
| `TWITTER_CLIENT_ID` | No | Twitter OAuth 2.0 client ID |
| `TWITTER_CLIENT_SECRET` | No | Twitter OAuth 2.0 client secret |
| `TWITTER_REDIRECT_URI` | No | Twitter OAuth callback URL |
| `TWITTER_BEARER_TOKEN` | No | Twitter bearer token for app-only requests |
| `TELEGRAM_API_ID` | No | Telegram MTProto API ID (integer) |
| `TELEGRAM_API_HASH` | No | Telegram MTProto API hash |
| `ANTHROPIC_API_KEY` | No | Anthropic API key for Claude AI features |
| `NEXT_PUBLIC_API_URL` | No | Backend base URL used by the Next.js frontend (default: `http://localhost:8000`). Set this when deploying frontend and backend to different hosts. |

---

## Project Structure

```
pingcrm/
├── README.md
├── CLAUDE.md                  # AI assistant instructions
├── mvp.md                     # Product specification
├── chrome-extension/          # LinkedIn companion Chrome extension (MV3)
├── docs/                      # Docusaurus documentation site
│
├── backend/                   # Python/FastAPI backend
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry point + middleware
│   │   ├── api/                     # Route handlers
│   │   │   ├── auth.py              # Google OAuth + email/password auth
│   │   │   ├── contacts.py          # Composition root — includes sub-routers
│   │   │   ├── contacts_routes/     # Contact route sub-modules
│   │   │   │   ├── crud.py          # Create, read, update, delete
│   │   │   │   ├── listing.py       # Paginated list + search
│   │   │   │   ├── taxonomy.py      # Tags + stats
│   │   │   │   ├── imports.py       # CSV + LinkedIn import
│   │   │   │   ├── sync.py          # Google/Telegram/Twitter sync dispatch
│   │   │   │   ├── duplicates.py    # Duplicate detection + merge
│   │   │   │   ├── messaging.py     # Interaction timeline + message send
│   │   │   │   └── shared.py        # Shared dependencies (router guards etc.)
│   │   │   ├── interactions.py      # Interaction timeline endpoints
│   │   │   ├── suggestions.py       # Follow-up suggestions
│   │   │   ├── telegram.py          # Telegram auth + sync + common groups
│   │   │   ├── twitter.py           # Twitter OAuth PKCE + sync
│   │   │   ├── organizations.py     # Organization CRUD + merge
│   │   │   ├── identity.py          # Identity resolution endpoints
│   │   │   ├── notifications.py     # Notification management
│   │   │   └── linkedin.py          # LinkedIn push endpoint + avatar download
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── contact.py
│   │   │   ├── contact_merge.py     # Merge audit trail
│   │   │   ├── interaction.py
│   │   │   ├── detected_event.py
│   │   │   ├── follow_up.py         # FollowUpSuggestion model
│   │   │   ├── identity_match.py
│   │   │   ├── organization.py
│   │   │   ├── notification.py
│   │   │   └── google_account.py
│   │   ├── schemas/                 # Pydantic request/response schemas (typed Envelope[T])
│   │   ├── services/                # Business logic
│   │   │   ├── tasks.py             # Re-export shim — backward-compatible Celery task names
│   │   │   ├── task_jobs/           # Celery task sub-modules by domain
│   │   │   │   ├── common.py        # Shared notify helpers
│   │   │   │   ├── gmail.py         # Gmail sync tasks
│   │   │   │   ├── telegram.py      # Telegram sync tasks
│   │   │   │   ├── twitter.py       # Twitter poll + DM sync tasks
│   │   │   │   ├── google.py        # Google Contacts + Calendar tasks
│   │   │   │   ├── scoring.py       # Relationship score tasks
│   │   │   │   ├── followups.py     # Suggestion generation tasks
│   │   │   │   ├── maintenance.py   # Snooze reactivation + org stats
│   │   │   │   └── tagging.py       # Auto-tagging tasks
│   │   │   ├── followup_engine.py   # Follow-up suggestion generation
│   │   │   ├── identity_resolution.py  # Cross-platform matching
│   │   │   ├── message_composer.py  # AI message drafting via Claude
│   │   │   ├── event_classifier.py  # LLM-based event classification
│   │   │   ├── contact_search.py    # Contact search/filter logic
│   │   │   ├── contact_import.py    # CSV/LinkedIn import logic
│   │   │   ├── bio_refresh.py       # Twitter bio refresh service
│   │   │   ├── telegram_service.py  # Telegram orchestration
│   │   │   ├── digest_email.py      # Weekly digest email
│   │   │   ├── scoring.py           # Relationship score calculation
│   │   │   └── notifications.py     # Notification creation helpers
│   │   ├── integrations/            # Third-party API clients
│   │   │   ├── gmail.py             # Gmail thread sync
│   │   │   ├── google_auth.py       # Google OAuth helpers
│   │   │   ├── google_calendar.py   # Calendar event sync
│   │   │   ├── telegram.py          # Telethon MTProto client
│   │   │   ├── twitter.py           # Twitter API v2 client
│   │   │   ├── bird.py              # Bird CLI (@steipete/bird) wrapper
│   │   │   └── linkedin.py          # LinkedIn avatar download
│   │   └── core/                    # Config, auth, database, encryption, Redis, Celery
│   ├── alembic/                     # Database migrations
│   ├── tests/                       # 631 pytest tests
│   ├── worker.py                    # Celery entry point
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/                  # Next.js 15 frontend
    ├── src/
    │   ├── app/                     # App Router pages
    │   │   ├── dashboard/           # Main dashboard
    │   │   ├── contacts/            # Contact list + new
    │   │   │   └── [id]/            # Contact detail page
    │   │   │       ├── _components/ # Detail UI components (timeline, panels, cards)
    │   │   │       ├── _hooks/      # Controller hook (use-contact-detail-controller)
    │   │   │       └── _lib/        # Helper utilities (formatters)
    │   │   ├── organizations/       # Organization list + detail (inline editing)
    │   │   ├── suggestions/         # Follow-up suggestions
    │   │   ├── identity/            # Identity resolution UI
    │   │   ├── notifications/       # Notification center
    │   │   ├── settings/            # Platform connections + CSV import
    │   │   │   ├── _components/     # Per-tab UI components (platform cards, import, tags)
    │   │   │   └── _hooks/          # Controller hooks (settings, Telegram connect flow)
    │   │   ├── onboarding/          # New user guided setup
    │   │   ├── auth/                # Login, register, OAuth callbacks
    │   │   ├── error.tsx            # Error boundary
    │   │   ├── global-error.tsx     # Root error boundary
    │   │   └── not-found.tsx        # 404 page
    │   ├── components/              # Reusable UI components
    │   │   ├── timeline.tsx         # Interaction timeline
    │   │   ├── editable-field.tsx   # Inline editing components
    │   │   ├── score-badge.tsx      # Relationship score badge
    │   │   ├── csv-import.tsx       # CSV drag-and-drop importer
    │   │   ├── empty-state.tsx      # Empty state placeholder
    │   │   ├── message-editor.tsx   # AI message editor
    │   │   └── nav.tsx              # Navigation bar with notification badge
    │   ├── hooks/                   # React Query data hooks
    │   │   ├── use-auth.ts          # Login, register, logout
    │   │   ├── use-contacts.ts      # Contact CRUD + search
    │   │   ├── use-dashboard.ts     # Dashboard stats
    │   │   ├── use-identity.ts      # Identity match operations
    │   │   ├── use-notifications.ts # Notification queries
    │   │   └── use-suggestions.ts   # Follow-up suggestions
    │   └── lib/                     # Typed API client (openapi-fetch), utilities
    ├── vitest.config.ts
    └── package.json
```

---

## API Reference

All endpoints return a standard envelope: `{ data, error, meta }`.

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register with email/password |
| POST | `/api/v1/auth/login` | Login with email/password |
| GET | `/api/v1/auth/me` | Get current authenticated user profile |
| GET | `/api/v1/auth/google/url` | Get Google OAuth authorization URL |
| POST | `/api/v1/auth/google/callback` | Exchange Google OAuth code for JWT |
| GET | `/api/v1/auth/google/accounts` | List connected Google accounts |
| DELETE | `/api/v1/auth/google/accounts/{id}` | Remove a connected Google account |
| GET | `/api/v1/auth/twitter/url` | Get Twitter OAuth 2.0 PKCE URL |
| POST | `/api/v1/auth/twitter/callback` | Exchange Twitter OAuth code for JWT |

### Contacts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/contacts` | List contacts (paginated, searchable, sortable, filterable) |
| POST | `/api/v1/contacts` | Create a contact |
| GET | `/api/v1/contacts/tags` | List all unique tags |
| GET | `/api/v1/contacts/stats` | Get contact statistics for dashboard |
| GET | `/api/v1/contacts/{id}` | Get contact detail |
| PUT | `/api/v1/contacts/{id}` | Update contact fields |
| DELETE | `/api/v1/contacts/{id}` | Delete a contact |
| GET | `/api/v1/contacts/{id}/duplicates` | Find potential duplicate contacts |
| POST | `/api/v1/contacts/{id}/merge/{other_id}` | Merge two contacts into one |
| POST | `/api/v1/contacts/{id}/refresh-bios` | Refresh Twitter/Telegram bios |
| POST | `/api/v1/contacts/import/csv` | Import contacts from CSV file |
| POST | `/api/v1/contacts/import/linkedin` | Import LinkedIn connections export |
| POST | `/api/v1/contacts/import/linkedin-messages` | Import LinkedIn messages export |
| POST | `/api/v1/contacts/scores/recalculate` | Recalculate all relationship scores |

### Sync (Background Tasks)

All sync endpoints dispatch Celery tasks and return immediately with `{ "status": "started" }`. A notification is created when the sync completes or fails.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/contacts/sync/google` | Sync Google Contacts (background) |
| POST | `/api/v1/contacts/sync/google-calendar` | Sync Google Calendar events (background) |
| POST | `/api/v1/contacts/sync/telegram` | Sync Telegram chats + groups + bios (background) |
| POST | `/api/v1/contacts/sync/twitter` | Sync Twitter DMs + mentions + bios (background) |

### Telegram Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/telegram/connect` | Send OTP to phone number |
| POST | `/api/v1/auth/telegram/verify` | Verify OTP code |
| POST | `/api/v1/auth/telegram/verify-2fa` | Complete 2FA password verification |
| POST | `/api/v1/auth/telegram/sync` | Sync Telegram chats (background) |
| GET | `/api/v1/contacts/{id}/telegram/common-groups` | Get shared Telegram groups with a contact |

### Interactions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/contacts/{id}/interactions` | Get interaction timeline for a contact |
| POST | `/api/v1/contacts/{id}/interactions` | Add a manual interaction/note |
| PATCH | `/api/v1/contacts/{id}/interactions/{iid}` | Update a manual note |
| DELETE | `/api/v1/contacts/{id}/interactions/{iid}` | Delete a manual note |

### Suggestions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/suggestions` | List follow-up suggestions |
| GET | `/api/v1/suggestions/digest` | Get weekly digest suggestions |
| PUT | `/api/v1/suggestions/{id}` | Update suggestion status (snooze/dismiss/send) |
| POST | `/api/v1/suggestions/generate` | Generate new AI-powered suggestions |
| POST | `/api/v1/suggestions/{id}/regenerate` | Regenerate AI message for a suggestion |

### Identity Resolution

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/identity/matches` | List pending identity matches |
| POST | `/api/v1/identity/scan` | Trigger cross-platform identity scan |
| POST | `/api/v1/identity/matches/{id}/merge` | Merge matched contacts |
| POST | `/api/v1/identity/matches/{id}/reject` | Reject a false match |

### Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/notifications` | List all notifications (paginated) |
| GET | `/api/v1/notifications/unread-count` | Get unread notification count |
| PUT | `/api/v1/notifications/{id}/read` | Mark a notification as read |
| PUT | `/api/v1/notifications/read-all` | Mark all notifications as read |

### Organizations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/organizations` | List organizations (paginated, searchable) |
| POST | `/api/v1/organizations/merge` | Merge multiple organizations into one |
| GET | `/api/v1/organizations/{id}` | Get organization detail with contacts |
| PATCH | `/api/v1/organizations/{id}` | Update organization fields |
| DELETE | `/api/v1/organizations/{id}` | Delete organization (unlinks contacts) |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | API health check |

---

## Celery Beat Schedule

| Task | Interval |
|------|----------|
| Gmail sync (all users) | Every 6 hours |
| Google Calendar sync (all users) | Daily (06:00 UTC) |
| Telegram sync (all users) | Daily (03:00 UTC) -- chats only; groups/bios on-demand |
| Telegram bio recheck (non-2nd-tier) | Every 3 days (05:00 UTC) |
| Twitter activity + DM poll | Daily (04:00 UTC) |
| Relationship score recalculation | Daily (02:00 UTC) |
| Follow-up suggestion generation | Daily (08:00 UTC) |
| Weekly digest email | Weekly (Monday 09:00 UTC) |
| Snooze reactivation | Hourly |
| Organization stats refresh | Hourly |

---

## Testing

```bash
# Backend tests (631 tests)
cd backend
pytest

# With coverage report
pytest --cov=app --cov-report=term-missing

# Frontend tests
cd frontend
npm test

# Frontend tests with watch mode
npm run test:watch
```

---

## License

Private / All rights reserved.
