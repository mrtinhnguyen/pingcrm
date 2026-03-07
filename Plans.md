# Plans - Ping CRM

> Phases 1-7 (101 tasks, all ✅) archived in [Plans-archive.md](Plans-archive.md)

## Phase 8: Security & Correctness Fixes

作成日: 2026-03-07

### 8.1 Google OAuth State Enforcement (High)

- [x] `cc:完了` Enforce state-bound user identity in Google callback: when `popped` value is a real user_id (not `__anonymous__`), verify it matches the current authenticated user before proceeding
- [x] `cc:完了` Add tests: state with user_id mismatch returns 403, anonymous state allows normal signup/login flow

### 8.2 Frontend Token Key Mismatch (High)

- [x] `cc:完了` Fix Google callback page to store JWT under `access_token` key, matching `api-client.ts` and `use-auth.ts`
- [x] `cc:完了` Add test for Google callback: verify token is stored under `access_token` key

### 8.3 Exception Detail Redaction (High)

- [x] `cc:完了` Replace raw `{exc}` in HTTPException details with generic user-facing messages; log the full exception server-side
- [x] `cc:完了` Add tests: verify error responses do not contain exception class names or tracebacks

### 8.4 Twitter Polling Filter (Medium)

- [x] `cc:完了` Filter `poll_twitter_all()` query to only users with `twitter_refresh_token IS NOT NULL`
- [x] `cc:完了` Add test: `poll_twitter_all` only enqueues tasks for Twitter-connected users

### 8.5 ENCRYPTION_KEY Startup Validation (Medium)

- [x] `cc:完了` Add startup validation for `ENCRYPTION_KEY` in `main.py` (warn in dev, error in production)
- [x] `cc:完了` Add `ENCRYPTION_KEY` to `.env.example` with generation command comment
- [x] `cc:完了` Add test: app startup raises when `ENCRYPTION_KEY` is empty and environment is production

### 8.6 Transaction Auto-Commit Documentation (Medium)

- [x] `cc:完了` Add inline docstring to `get_db()` explaining the auto-commit policy
- [x] `cc:完了` Add `# TRANSACTION POLICY` comment block at top of `database.py`
