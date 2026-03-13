# Fix Telegram Sync Timeouts (Issue #30)

Created: 2026-03-13
Completed: 2026-03-13

---

## Context

`sync_telegram_chats_for_user` iterates ALL dialogs (~1000 for this user) with no cap.
At ~4.5s/dialog, that's ~75 min — far exceeding the 20-min hard limit.

**Strategy:** Chunked initial sync + incremental daily sync (most recent 100 dialogs).

- First run: chunk all dialogs into batches of 50, each batch is a separate Celery task
- Subsequent runs: only process 100 most-recent dialogs (fast, fits in time limit)
- Track `telegram_last_synced_at` on User to distinguish first vs. incremental sync

---

## Phase 1: Track sync state

| Task | Description | DoD | Depends | Status |
|------|-------------|-----|---------|--------|
| 1.1 | Add `telegram_last_synced_at: DateTime` column to User model + Alembic migration | Migration runs; column exists in DB | - | cc:完了 |

---

## Phase 2: Chunked initial sync

| Task | Description | DoD | Depends | Status |
|------|-------------|-----|---------|--------|
| 2.1 | Create `collect_dialog_ids(user)` helper in `telegram.py` — iterate all dialogs, return list of dicts with entity_id/username/name/phone, filtering bots/channels. No message fetching. | Returns list; completes in <60s for 1000 dialogs | 1.1 | cc:完了 |
| 2.2 | Create `sync_telegram_chats_batch(user, entity_ids, db)` in `telegram.py` + `sync_telegram_chats_batch_task` Celery task — process a batch of ~50 dialogs (message fetch + upsert + avatar queue). | Task completes within 5 min for 50 dialogs | 2.1 | cc:完了 |
| 2.3 | Refactor `sync_telegram_for_user()` — if `telegram_last_synced_at` is NULL (first sync): collect all dialog IDs, chunk into batches of 50, dispatch as a Celery chain of batch tasks + groups + bios + notify. | First sync dispatches N/50 batch tasks; all complete without timeout | 2.2 | cc:完了 |

---

## Phase 3: Incremental daily sync

| Task | Description | DoD | Depends | Status |
|------|-------------|-----|---------|--------|
| 3.1 | Modify `sync_telegram_chats()` to accept `max_dialogs: int` parameter — break out of `iter_dialogs()` after processing N dialogs. Update `telegram_last_synced_at` on completion. | Incremental sync processes ≤100 dialogs; completes in <8 min | 2.3 | cc:完了 |
| 3.2 | Update `sync_telegram_for_user()` — if `telegram_last_synced_at` is set (incremental): use existing single-task flow with `max_dialogs=100` | Daily beat sync runs fast; no timeout | 3.1 | cc:完了 |

---

## Phase 4: Groups & bios time limit fix

| Task | Description | DoD | Depends | Status |
|------|-------------|-----|---------|--------|
| 4.1 | Increase `sync_telegram_groups_for_user` limits to `soft_time_limit=600, time_limit=900`. Increase `sync_telegram_bios_for_user` to `soft_time_limit=600, time_limit=900`. | Tasks don't timeout for accounts with up to 30 groups / 100 contacts | - | cc:完了 |

---

## Notes

- Dialog collection (`iter_dialogs()`) is fast (~30s for 1000) — it's the message fetching per dialog that's slow
- Batches of 50 dialogs ≈ 3.5–4.5 min each (within 5-min soft limit with margin)
- Incremental sync (100 most-recent dialogs) ≈ 7.5 min — fits in current 15-min soft limit
- `telegram_last_synced_at` also useful for showing "Last synced: X hours ago" in Settings UI
- Avatar downloads stay batched per-task (already post-loop)
