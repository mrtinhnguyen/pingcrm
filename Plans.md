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

---

## Phase 9: AI Auto-Tagging + Maintenance

作成日: 2026-03-08

### 9.1 AI Auto-Tagging Feature (Done)

- [x] `cc:完了` TagTaxonomy model + migration (tag_taxonomies table)
- [x] `cc:完了` auto_tagger.py service (discover_taxonomy, assign_tags, merge_tags)
- [x] `cc:完了` API endpoints: /tags/discover, /tags/taxonomy GET/PUT, /tags/apply, /{id}/auto-tag
- [x] `cc:完了` Celery task: apply_tags_to_contacts for bulk tagging
- [x] `cc:完了` Frontend: Tags taxonomy page with discover/edit/approve/apply flow
- [x] `cc:完了` Frontend: Auto-tag kebab menu on contact detail page
- [x] `cc:完了` Nav: Tags link with correct isActive logic
- [x] `cc:完了` Review fixes: route ordering, N+1 queries, prompt injection sanitization, status validation
- [x] `cc:完了` Fix deprecated Haiku model ID (claude-3-5-haiku → claude-haiku-4-5)

### 9.2 Missing Tests: auto_tagger.py (Medium)

- [x] `cc:完了` Unit tests for merge_tags (case-insensitive dedup, append-only)
- [x] `cc:完了` Unit tests for _build_contact_summary (sanitization, length caps)
- [x] `cc:完了` Unit tests for _parse_json_response (bare JSON, code fences, invalid)
- [x] `cc:完了` Unit tests for discover_taxonomy (mocked LLM, batching, error propagation)
- [x] `cc:完了` Unit tests for assign_tags (taxonomy validation, case matching)

### 9.3 Login Endpoint Envelope Consistency (Low)

- [x] `cc:完了` Wrap /login response in Envelope[TokenData] to match all other endpoints
