# Plans - Ping CRM

> Phases 1-7 (101 tasks, all done) archived in [Plans-archive.md](Plans-archive.md)
> Phases 8-9 (all done) — Security fixes, AI auto-tagging, test coverage

---

## Phase 10: Maintenance & Polish

作成日: 2026-03-08

### 10.1 Commit In-Progress Work (High)

- [ ] `cc:WIP` Commit and push: Labels→Tags rename (#10), Contacts nav submenu with Archive page (#11)
- [ ] `cc:TODO` Close GitHub issues #10 and #11

### 10.2 Archive Page Suspense Wrapper (Medium)

- [ ] `cc:TODO` Wrap `/contacts/archive/page.tsx` in `<Suspense>` boundary (same pattern as contacts page) — required by Next.js App Router for `useSearchParams()`

### 10.3 TypeScript Errors Cleanup (Medium)

- [ ] `cc:TODO` Fix 4 pre-existing TS errors: `contacts/[id]/page.tsx` (2 errors — birthday field type), `settings/page.tsx` (1 error — POST call signature), `auth/google/callback/page.test.tsx` (1 error)

### 10.4 Frontend Test Coverage Expansion (Medium)

- [ ] `cc:TODO` Add tests for nav component (dropdown rendering, active state, submenu links)
- [ ] `cc:TODO` Add tests for archive page (renders, search, unarchive button)
- [ ] `cc:TODO` Add tests for identity page (scan, merge flow)

### 10.5 PKCE Verifier Storage (Medium)

- [ ] `cc:TODO` Move Twitter PKCE verifiers from in-memory dict to Redis (required for multi-worker production deployment)

### 10.6 Celery Beat Schedule Review (Low)

- [ ] `cc:TODO` Verify Telegram sync interval (12h) is appropriate post-split into 3 sub-tasks
- [ ] `cc:TODO` Consider adding Google Calendar sync to beat schedule (currently manual-only)

### 10.7 Docker Deployment (Low)

- [ ] `cc:TODO` Create `docker-compose.yml` with PostgreSQL, Redis, backend, frontend, Celery worker, Celery beat
- [ ] `cc:TODO` Create `Dockerfile` for backend and frontend

### 10.8 OpenAPI Schema Regeneration (Low)

- [ ] `cc:TODO` Regenerate `backend/openapi.json` and `frontend` openapi-fetch types to include new `archived_only` param and any other recent API changes

---

## Backlog: Feature Exploration (from GitHub Issues)

| Issue | Title | Priority |
|-------|-------|----------|
| #7 | MCP Server integration | Explore |
| #6 | Pre-meeting prep notifications | Explore |
| #5 | Two-way device contact sync | Explore |
| #4 | Sync with WhatsApp, iMessage | Explore |
