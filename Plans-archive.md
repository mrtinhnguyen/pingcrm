# Plans Archive - Ping CRM

All completed phases archived from Plans.md.

## Phase 1: Foundation (Weeks 1-4) — 20 tasks ✅

### 1.1 Project Scaffolding
- [x] Initialize FastAPI backend project structure
- [x] Initialize Next.js frontend project
- [x] Set up PostgreSQL schema with Alembic migrations
- [x] Configure environment variables and settings

### 1.2 Auth & Onboarding
- [x] User auth (signup/login) with JWT
- [x] Google OAuth integration for Gmail + Contacts
- [x] Onboarding flow UI

### 1.3 Contact Management
- [x] Contact model and CRUD API endpoints
- [x] CSV import endpoint with field mapping
- [x] Google Contacts one-way sync
- [x] Manual contact creation UI
- [x] Contact profile page with unified fields

### 1.4 Gmail Integration
- [x] Gmail API thread sync service
- [x] Interaction tracking from email threads
- [x] Periodic sync job (Celery task)

### 1.5 Interaction Timeline
- [x] Interaction model and API
- [x] Timeline UI component (reverse chronological, grouped by platform)
- [x] Manual note entry

### 1.6 Basic Relationship Scoring
- [x] Scoring model implementation (signal-based points)
- [x] Score display on contact cards (green/yellow/red)

## Phase 2: Intelligence (Weeks 5-8) — 14 tasks ✅

### 2.1 Telegram Integration
- [x] MTProto client setup
- [x] Chat history sync
- [x] Contact matching from Telegram

### 2.2 Identity Resolution
- [x] Tier 1: Deterministic matching (email, phone)
- [x] Tier 4: User confirmation UI for low-confidence matches
- [x] IdentityMatch model and merge logic

### 2.3 Context Detection Engine
- [x] Twitter activity polling service
- [x] LLM classifier for event detection (job change, fundraising, etc.)
- [x] DetectedEvent model and storage

### 2.4 AI Message Composer
- [x] Message generation service (Claude API)
- [x] Tone and style adaptation from conversation history
- [x] Draft editing UI

### 2.5 Follow-Up Engine
- [x] FollowUpSuggestion model and generation logic
- [x] Time-based + event-based triggers
- [x] Weekly digest email (Celery scheduled task)

## Phase 3: Polish (Weeks 9-12) — 10 tasks ✅

### 3.1 Twitter Integration
- [x] Twitter DM and mention sync
- [x] Bio change monitoring

### 3.2 Dashboard
- [x] "Reach out this week" section
- [x] "Recent activity from your network" feed
- [x] "Relationship health overview" summary
- [x] "Recently contacted" list

### 3.3 Follow-Up Workflows
- [x] Snooze, schedule, dismiss actions
- [x] Notification system (in-app + email)

### 3.4 Identity Resolution v2
- [x] Tier 2: Probabilistic matching (scored)

### 3.5 Performance & Hardening
- [x] Optimize for 500+ contacts
- [x] Error states and edge case handling
- [x] Security audit (OAuth tokens, data access)

## Phase 4: Critical Fixes — 16 tasks ✅

### 4.1 Google OAuth CSRF Protection
- [x] Add `state` param to `GoogleCallbackRequest` schema and validate server-side
- [x] Store OAuth state nonce server-side (in-memory dict with TTL)
- [x] Pass `state` from frontend Google callback page to backend callback endpoint
- [x] Standardize frontend token key: always use `access_token` from response
- [x] Add tests for state validation (missing, invalid, expired)

### 4.2 Identity Merge Audit Trail
- [x] Create `contact_merges` table
- [x] Create Alembic migration for `contact_merges` table
- [x] Record merge in `contact_merges` before deleting secondary contact
- [x] Change `IdentityMatch.contact_b_id` FK to `SET NULL` on delete
- [x] Remove `db.expunge(match)` hack from merge_contacts
- [x] Add tests: merge audit record creation and survival

### 4.3 Suggestion Message Flows
- [x] Add `suggested_message` and `suggested_channel` fields to `SnoozeBody`
- [x] Persist edited `suggested_message` and `suggested_channel` in PUT
- [x] Add POST /suggestions/{id}/regenerate endpoint
- [x] Add `useRegenerateSuggestion` hook + Regenerate button
- [x] Add tests: update persists message/channel, regenerate returns new message

## Phase 5: Production Hardening — 15 tasks ✅

### 5.1 Redis State Migration
- [x] Add Redis client dependency and async connection helper
- [x] Migrate `_pkce_store` to Redis with 600s TTL
- [x] Migrate `_google_state_store` to Redis with 600s TTL
- [x] Migrate `_bio_check_cache` to Redis with 86400s TTL
- [x] Add tests for Redis state stores (fakeredis)

### 5.2 Transaction Boundary Cleanup
- [x] Document transaction policy: handlers flush(), get_db owns commit/rollback
- [x] Remove explicit db.commit() from API route handlers
- [x] Audit service-layer functions (confirmed flush-only)
- [x] All 245 tests pass — rollback verified

### 5.3 Query Optimization
- [x] Fix N+1 in list_suggestions and get_digest
- [x] Fix N+1 in send_weekly_digest
- [x] Fix broad-scan in list_pending_matches
- [x] Fix _match_to_dict N+1 with batch helper
- [x] Add blocking keys to find_probable_matches
- [x] Scope find_probabilistic_matches to user's contacts

## Phase 6: Architecture & Security Hardening — 14 tasks ✅

### 6.1 Token Encryption
- [x] Add Fernet EncryptedString TypeDecorator
- [x] Add Alembic migration to encrypt existing tokens in-place
- [x] Update model columns to use EncryptedString
- [x] Token redaction verified (boolean flags only in API responses)

### 6.2 Service Extraction
- [x] Extract contact_search.py (contacts.py: 783→447 lines)
- [x] Extract contact_import.py (CSV/LinkedIn)
- [x] Extract bio_refresh.py
- [x] Extract telegram_service.py
- [x] Remove private _-prefixed imports from API layer

### 6.3 Typed API Contracts
- [x] Typed response schemas for contacts endpoints
- [x] Typed response schemas for suggestions + identity + notifications
- [x] Typed response schemas for interactions + telegram + twitter + auth
- [x] OpenAPI client generation script (openapi-typescript + openapi-fetch)
- [x] Replace manual fetch/apiClient with generated typed client

## Phase 7: Async I/O, Dead Code Cleanup & Config Hygiene — 12 tasks ✅

### 7.1 Blocking LLM Calls → Async
- [x] Convert classify_tweet/classify_bio_change to AsyncAnthropic
- [x] Add concurrency semaphore (Semaphore(5))
- [x] Add exponential backoff + jitter on transient API errors
- [x] Update test_event_classifier.py for async signatures

### 7.2 Dead/Legacy Code Removal
- [x] Remove unused contact-card.tsx
- [x] Remove unused error-boundary.tsx
- [x] Remove old api.ts, migrate test mocks to api-client
- [x] Audit and remove other unreferenced components

### 7.3 Docs/Config Drift — Externalize Hosts
- [x] Externalize backend proxy URL via NEXT_PUBLIC_API_URL
- [x] Externalize CORS origins via settings.CORS_ORIGINS
- [x] Fix avatar URL construction to use NEXT_PUBLIC_API_URL
- [x] Sync README.md env vars table with config.py fields
