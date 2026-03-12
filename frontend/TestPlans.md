# Ping CRM Frontend — Test Coverage Plan

Created: 2026-03-11

---

## Current State

- **Framework:** Vitest + @testing-library/react + jsdom
- **Existing tests:** 10 files, 150 tests (all passing)
- **0 failing files** (Phase 1 complete)

### Failing Tests Root Causes
1. **contacts/page.test.tsx** (26 fails) — Missing `SlidersHorizontal` in lucide-react mock; page was redesigned with new columns, filters, select-all, etc.
2. **settings/page.test.tsx** (1 fail) — Import/setup error (likely missing mock or changed dependency)
3. **message-editor.test.tsx** (1 fail) — `onSend` callback signature changed

---

## Phase 1: Fix Broken Tests

| Task | Description | DoD | Depends | Status |
|------|-------------|-----|---------|--------|
| 1.1 | Update lucide-react mock in `setup.ts` — add all missing icons (`SlidersHorizontal`, `ArrowDown`, `ArrowUpDown`, `Filter`, etc.) | `contacts/page.test.tsx` renders without icon errors | - | cc:完了 |
| 1.2 | Fix `contacts/page.test.tsx` — update selectors for redesigned table (new column names, grid layout, select-all checkbox, stats header) | All 26 contacts page tests pass | 1.1 | cc:完了 |
| 1.3 | Fix `settings/page.test.tsx` — diagnose import error, update mocks/selectors for any redesigned UI | All 41 settings tests pass | 1.1 | cc:完了 |
| 1.4 | Fix `message-editor.test.tsx` — update `onSend` callback test to match current signature | `onSend` test passes | - | cc:完了 |

---

## Phase 2: Cover Redesigned Components

| Task | Description | DoD | Depends | Status |
|------|-------------|-----|---------|--------|
| 2.1 | Test `InlineField` (contact detail) — default state shows value/link, hover shows pencil, click pencil opens edit mode, Cancel/Save buttons, Enter/Escape keys | ≥8 tests covering view/edit/save/cancel/link modes | Phase 1 | cc:TODO |
| 2.2 | Test `InlineListField` — same patterns as InlineField but for arrays (emails, phones), displays "+N" for multiple values | ≥6 tests | Phase 1 | cc:TODO |
| 2.3 | Test `nav.tsx` — hover dropdown opens/closes with delay, links render correctly, search opens command palette, notification badge | ≥8 tests | Phase 1 | cc:TODO |
| 2.4 | Test `contact-avatar.tsx` — renders image when `avatar_url` exists, renders initials fallback, color mapping | ≥4 tests | Phase 1 | cc:TODO |

---

## Phase 3: Cover Untested Pages (High Priority)

| Task | Description | DoD | Depends | Status |
|------|-------------|-----|---------|--------|
| 3.1 | Test `dashboard/page.tsx` — stat cards render with loading/data states, pending follow-ups section, recent activity, empty state | ≥10 tests | Phase 2 | cc:TODO |
| 3.2 | Test `contacts/[id]/page.tsx` — header with name/avatar/tags, detail fields section, activity breakdown, kebab menu actions, duplicate card | ≥12 tests | 2.1, 2.2 | cc:TODO |
| 3.3 | Test `suggestions/page.tsx` — suggestion cards render, snooze/dismiss/send actions, scheduled message state | ≥8 tests | Phase 2 | cc:TODO |
| 3.4 | Test `contacts/archive/page.tsx` — loads archived contacts, unarchive button works, bulk select/unarchive, empty state | ≥6 tests | Phase 2 | cc:TODO |

---

## Phase 4: Cover Untested Pages (Medium Priority)

| Task | Description | DoD | Depends | Status |
|------|-------------|-----|---------|--------|
| 4.1 | Test `identity/page.tsx` — scan button, duplicate pairs list, merge/dismiss actions | ≥6 tests | Phase 3 | cc:TODO |
| 4.2 | Test `organizations/page.tsx` — org list renders, search, create org | ≥5 tests | Phase 3 | cc:TODO |
| 4.3 | Test `notifications/page.tsx` — notification list, mark read, empty state | ≥5 tests | Phase 3 | cc:TODO |
| 4.4 | Test `auth/register/page.tsx` — form validation, submit, redirect | ≥5 tests | Phase 3 | cc:TODO |
| 4.5 | Test `contacts/new/page.tsx` — form fields, submit creates contact, validation | ≥5 tests | Phase 3 | cc:TODO |

---

## Phase 5: Cover Remaining Components & Utilities

| Task | Description | DoD | Depends | Status |
|------|-------------|-----|---------|--------|
| 5.1 | Test `activity-breakdown.tsx` — score dimensions render, monthly trend chart, stats section | ≥5 tests | Phase 4 | cc:TODO |
| 5.2 | Test `csv-import.tsx` — file upload, preview table, column mapping, submit | ≥6 tests | Phase 4 | cc:TODO |
| 5.3 | Test `tag-taxonomy-panel.tsx` — tag list, add/remove/rename, category grouping | ≥5 tests | Phase 4 | cc:TODO |
| 5.4 | Test hooks (`use-contacts`, `use-dashboard`, `use-suggestions`) — query key correctness, data transformation, error states | ≥8 tests | Phase 4 | cc:TODO |

---

## Notes

- **Testing approach:** Behavior-driven (no snapshots), user-centric selectors (roles, labels), async-aware
- **Mock strategy:** Mock API client at module level, mock hooks for page-level tests, test components in isolation
- **Priority:** Phase 1 (fix broken) → Phase 2 (redesigned components) → Phase 3 (high-traffic pages) → Phase 4-5 (coverage)
- **Estimated total new tests:** ~120 across all phases
- **Target:** 0 failing tests after Phase 1, >70% component coverage after Phase 3
