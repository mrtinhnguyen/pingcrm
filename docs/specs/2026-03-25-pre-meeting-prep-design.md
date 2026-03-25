# Pre-Meeting Prep Email Notifications

**Date:** 2026-03-25
**Issue:** #6
**Status:** Approved

## Problem

When a user has an upcoming Google Calendar meeting with someone they've interacted with before, they want context about that person — profile, interaction history, relationship health, and suggested talking points — delivered to their email 30 minutes before the meeting.

## Solution

A Celery beat task scans for upcoming meetings every 10 minutes. When a meeting is 30-40 minutes away, it gathers attendee context from existing contact data, generates AI talking points via Claude Haiku, and sends an HTML prep brief email via the Gmail API using the user's own OAuth token.

## Architecture

```
Celery beat (every 10 min)
  → scan_upcoming_meetings()
    → for each meeting starting in 30-40 min:
      → match attendee emails to contacts
      → gather context (bios, interactions, score)
      → generate talking points (Claude Haiku)
      → compose HTML email
      → send via Gmail API (users.messages.send)
      → mark as sent (Redis dedup key, 24h TTL)
```

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Trigger frequency | Every 10 min via Celery beat | Simple, catches meetings within window without real-time complexity |
| Send window | 30-40 min before meeting start | 10-min window prevents duplicates naturally across beat runs |
| Dedup | Redis key `meeting_prep:{user_id}:{event_id}` with 24h TTL | Prevents re-sending on task retries or overlapping runs |
| Email source | User's Gmail via OAuth (gmail.send scope) | No third-party service; email comes from user's own address |
| AI model | Claude Haiku | Fast, cheap (~$0.005/meeting) for talking point generation |
| Email format | HTML | Reuse pattern from existing weekly digest email builder |

## OAuth Scope Change

### Current scopes
```
openid email profile
https://www.googleapis.com/auth/contacts.readonly
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/calendar.readonly
```

### New scope to add
```
https://www.googleapis.com/auth/gmail.send
```

### Re-authorization flow
- Add `gmail.send` to the scope list in `google_auth.py` (which already has `include_granted_scopes="true"`, so existing read-only tokens continue working)
- Existing users: when `gmail.send` is needed but not granted, create a notification: "Gmail permissions updated — please re-authorize to enable pre-meeting prep emails"
- Re-auth redirects to Google consent screen showing the new permission
- On callback, store the updated refresh token

## Email Content (Prep Brief)

```
Subject: Meeting prep: {event_title} in 30 minutes

━━━ Meeting ━━━
{title} — {time} — {location/meet link}

━━━ Attendees ━━━

For each known contact:

  {avatar} {name} — {title} at {company}
  Score: {Strong/Warm/Cold} · {interaction_count} interactions
  Last contact: {date} via {platform}

  Latest bios:
  - Twitter: {twitter_bio}
  - LinkedIn: {linkedin_headline} — {linkedin_bio}
  - Telegram: {telegram_bio}
  (Platform bios shown only when available)

  Recent interactions (last 3-5):
  - {date}: {preview} ({platform})
  - {date}: {preview} ({platform})
  - {date}: {preview} ({platform})

For unknown attendees (email not matching any contact):
  {name or email} — No prior interactions recorded.

━━━ Suggested talking points ━━━
(Claude Haiku-generated based on attendee profiles + interaction history)
- {point 1}
- {point 2}
- {point 3}
```

## Data Sources for Prep Brief

| Data | Source | Already available? |
|------|--------|-------------------|
| Meeting title, time, attendees | Google Calendar sync (Interaction records with platform="meeting") | Yes — syncs 30 days forward |
| Contact name, title, company | Contact model | Yes |
| Relationship score | Contact.relationship_score | Yes |
| Twitter bio | Contact.twitter_bio | Yes |
| LinkedIn headline + bio | Contact.linkedin_headline, Contact.linkedin_bio | Yes |
| Telegram bio | Contact.telegram_bio | Yes |
| Recent interactions | Interaction model (last 5, ordered by occurred_at) | Yes |
| Common Telegram groups | Contact.telegram_common_groups | Yes |
| Avatar | Contact.avatar_url | Yes |
| AI talking points | Claude Haiku API call | New — uses existing Anthropic SDK |

## Components to Build

### 1. Gmail Send Service (`backend/app/integrations/gmail_send.py`)
- `send_email(user, subject, html_body)` — **sync** function (not async), sends via Gmail API
- Uses `google-api-python-client` (already in requirements) — `googleapiclient` is blocking I/O, consistent with existing `_build_gmail_service` pattern
- Called from within Celery task's async wrapper (same pattern as all other Google API calls)
- Sends to the user's own email address (self-prep brief)
- Uses the GoogleAccount that owns the calendar where the meeting lives
- Handles OAuth token refresh if needed (catches `google.auth.exceptions.RefreshError`)
- Returns success/failure

### 2. Meeting Prep Composer (`backend/app/services/meeting_prep.py`)
- `get_upcoming_meetings(user_id, window_start, window_end, db)` — queries Interaction records with platform="meeting" in the time window. **Groups by event ID** (extracted from `raw_reference_id` prefix `gcal:{event_id}:*`) to reconstruct the full attendee list per meeting. Returns list of `(event_id, event_title, event_time, list[contact_id])`.
- `build_prep_brief(user, contacts, db)` — gathers contact context (bios, interactions, score)
- `generate_talking_points(contact_context)` — Claude Haiku (`claude-haiku-4-5-20251001`) call for AI talking points
- `compose_prep_email(meeting, attendee_briefs, talking_points)` — renders HTML email

### 3. Celery Beat Task (`backend/app/services/task_jobs/meeting_prep.py`)
- `scan_and_send_meeting_preps()` — runs every 10 min
- Scans for meetings in 30-40 min window
- Deduplicates via Redis
- Calls composer + Gmail send
- **Must be registered** in `backend/app/services/tasks.py` (re-export module) and added to `test_task_registry.py` expected task list

### 4. OAuth Scope Update (`backend/app/api/auth.py`)
- Add `gmail.send` to Google OAuth scope list
- Handle re-authorization notification for existing users

### 5. User Setting (`backend/app/api/settings.py`)
- Toggle: "Send pre-meeting prep emails" (default: ON for users with Gmail connected)
- Stored in `User.sync_settings` JSONB (key: `meeting_prep_enabled`)

## Gmail API Send Implementation

```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
from email.mime.text import MIMEText

def send_email(google_account, subject, html_body):
    """Sync function — called from Celery task async wrapper.
    Uses the GoogleAccount that owns the calendar event."""
    creds = Credentials(
        token=None,
        refresh_token=google_account.refresh_token,
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
    )
    service = build("gmail", "v1", credentials=creds)
    message = MIMEText(html_body, "html")
    message["to"] = google_account.email  # user sends to themselves
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()
```

**Multi-account note:** Users may have multiple Google accounts connected (via `GoogleAccount` model). The prep email is sent from the account that owns the calendar where the meeting lives. The task iterates `GoogleAccount` entries per user (same pattern as calendar sync in `task_jobs/google.py`).

## Celery Beat Schedule

```python
"scan-meeting-preps-every-10m": {
    "task": "app.services.tasks.scan_meeting_preps",
    "schedule": crontab(minute="*/10"),
},
```

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Gmail send fails (network) | Log error, skip this meeting, will retry on next beat run if still in window |
| Gmail send fails (auth/scope) | Create notification: "Re-authorize Gmail for meeting prep emails", skip |
| Token refresh fails (`google.auth.exceptions.RefreshError`) | Token revoked — create notification to re-authorize, skip this account |
| Claude API fails | Send email without talking points section (graceful degradation) |
| No known attendees | Skip sending (no value in an empty prep brief) |
| Meeting cancelled between sync and send | Gmail API may return error, caught and logged |

## Out of Scope

- In-app meeting prep UI (follow-up issue)
- Calendar push notifications (webhooks instead of polling)
- Multi-calendar support (only primary calendar)
- Customizable send window (hardcoded 30 min)
- Recurring meeting dedup (each instance treated separately, which is correct — attendees may change)

## Testing

- Unit tests for `build_prep_brief` with mocked contact data
- Unit test for `compose_prep_email` HTML output
- Unit test for `scan_and_send_meeting_preps` with mocked Gmail API
- Integration test for OAuth scope upgrade flow
- Test dedup: same meeting doesn't trigger twice
- Test: meeting with only unknown attendees → skip sending
- Test: user with `meeting_prep_enabled: false` → skip
- Test: Claude API timeout → email sent without talking points (graceful degradation)
- Test: task registered in `tasks.py` and beat schedule (test_task_registry)
