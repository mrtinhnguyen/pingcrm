---
sidebar_position: 11
title: LinkedIn Integration
---

# LinkedIn Integration

Ping CRM syncs LinkedIn messages and profiles through a Chrome extension. The extension calls LinkedIn's internal Voyager API directly from your browser — no LinkedIn credentials are sent to the backend.

## Extension Pairing

Connecting the extension uses a one-time pairing code instead of a password:

1. Install the Ping CRM Chrome extension.
2. Open the extension popup — it displays a code like `PING-X7K3M2`.
3. Open Ping CRM **Settings → Integrations → LinkedIn** and click **Connect**.
4. Enter the code in the modal and click **Pair**.
5. The extension polls the backend and, once matched, shows **Connected**.

Pairing codes expire after 10 minutes. The issued token is valid for 30 days; when it expires, the popup prompts you to re-pair with a new code.

## Message Sync

Messages are fetched via LinkedIn's Voyager GraphQL API, called directly from the extension's service worker. This provides access to full conversation history, not just whatever is visible on the page.

On each sync the extension reads your LinkedIn session cookies from the browser, fetches conversations sorted by most-recent activity, and stops paginating once it reaches messages already seen in a previous sync (the **watermark**). Parsed results are pushed to the backend; LinkedIn cookies are never included.

A **2-hour throttle** prevents excessive syncs during a browsing session. The popup's **Sync Now** button bypasses the throttle for an immediate sync.

## What Gets Synced

The extension syncs contacts you have **LinkedIn conversations** with. If you've exchanged messages with someone, they become a contact in Ping CRM with their most recent message, profile info, and avatar.

**Synced automatically:**
- Contacts you've messaged (inbound and outbound)
- Profile data (name, headline, company, location, avatar) via Voyager API backfill
- Up to 500 conversations per sync cycle

**Not synced:**
- LinkedIn connections you've never messaged
- Profiles you browse but don't message
- Group chat messages

## Profile Backfill

After each sync, the backend identifies contacts missing a job title, company, or avatar. The extension then fetches those profiles via the Voyager API and pushes the enriched data back — up to 10 profiles per sync cycle. No manual profile visits required.

Voyager profile responses include CDN URLs for profile photos at multiple resolutions. The backend downloads the images server-side, so contacts you've messaged but never visited on LinkedIn receive avatars automatically.

## Importing Full History

For a complete import of your LinkedIn network (including connections you haven't messaged), use LinkedIn's data export:

1. Go to [LinkedIn Data Export](https://www.linkedin.com/mypreferences/d/download-my-data) and request your data
2. Download the archive when ready (usually takes ~24 hours)
3. Extract `Connections.csv` from the archive
4. In Ping CRM, go to **Contacts → Import** and upload the CSV

This imports all your 1st-degree connections with names, companies, positions, and email addresses. The extension's Voyager sync will then enrich these contacts with avatars and recent message history on subsequent syncs.

## Privacy

LinkedIn session cookies (`li_at` and `JSESSIONID`) are read fresh from your browser at the start of every sync and are used only to authenticate Voyager API calls made from the extension itself. They are never transmitted to the Ping CRM backend. All Voyager requests originate from your browser and your IP address, indistinguishable from normal LinkedIn browsing.

## Sync Schedule

| Trigger | Behavior |
|---|---|
| Any LinkedIn page visit | Syncs if more than 2 hours have passed since the last sync |
| Manual "Sync Now" (popup) | Syncs immediately, no throttle |

Sync is purely event-driven — no background alarms or scheduled tasks are needed. If your LinkedIn session expires, the popup shows a prompt to visit linkedin.com so the extension can pick up fresh cookies automatically on your next page visit.
