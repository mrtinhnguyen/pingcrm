# Fix "Event loop is closed" in sync task retries (Issue #32)

Created: 2026-03-13
Completed: 2026-03-13

---

## Context

When a sync task (Twitter, Telegram, Gmail) fails on the final retry, the exception handler calls `_run(_notify_sync_failure(...))` to create a user notification. But `_run()` uses `asyncio.run()` which closes the event loop after each call. The first `_run()` (the sync itself) already closed the loop, so the second `_run()` (notification) fails with `RuntimeError: Event loop is closed`.

**Strategy:** Two-pronged fix:
1. Make `_run()` defensively create a fresh event loop each time (belt)
2. Convert notification helpers into proper Celery tasks using `.delay()` (suspenders)

**Affected tasks:** 7 sync tasks + 2 tagging tasks = 9 exception handlers total.

---

## Phase 1: Fix `_run()` helper

| Task | Description | DoD | Depends | Status |
|------|-------------|-----|---------|--------|
| 1.1 | Rewrite `_run()` to use `asyncio.new_event_loop()` + `try/finally close()` instead of `asyncio.run()` | Sequential `_run()` calls in same thread don't raise "Event loop is closed" | - | cc:完了 |

---

## Phase 2: Decouple notifications into Celery tasks

| Task | Description | DoD | Depends | Status |
|------|-------------|-----|---------|--------|
| 2.1 | Create `notify_sync_failure` as `@shared_task` — accepts `user_id`, `platform`, `error` strings, creates Notification row. Remove async `_notify_sync_failure()` helper. | Task runs independently; notification row created in DB | 1.1 | cc:完了 |
| 2.2 | Create `notify_tagging_failure` as `@shared_task` — accepts `user_id`, `error` strings, creates Notification row. Remove async `_notify_tagging_failure()` helper. | Task runs independently; notification row created in DB | 1.1 | cc:完了 |
| 2.3 | Replace all 7 `_run(_notify_sync_failure(...))` calls in exception handlers with `notify_sync_failure.delay(str(uid), platform, str(exc))` | No `_run()` calls remain in exception handlers for sync tasks | 2.1 | cc:完了 |
| 2.4 | Replace 2 `_run(_notify_tagging_failure(...))` calls in exception handlers with `notify_tagging_failure.delay(str(uid), str(exc))` | No `_run()` calls remain in exception handlers for tagging tasks | 2.2 | cc:完了 |

---

## Notes

- Notification tasks are fire-and-forget (`.delay()`), so even if the sync task crashes hard the notification is enqueued
- The new tasks are synchronous (use `_run()` internally) — simple and consistent with existing pattern
- `_run()` fix is belt-and-suspenders: prevents the same class of bug from hitting any future `_run()` calls
- No new dependencies needed (no `nest_asyncio`)
