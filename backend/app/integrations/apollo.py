"""Apollo People Enrichment API client."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def enrich_person(
    email: str | None = None,
    linkedin_url: str | None = None,
) -> dict[str, Any]:
    """Call Apollo People Match API and return normalized contact fields.

    Accepts either an email or a LinkedIn URL as the lookup identifier.
    When both are provided, email takes priority (higher match quality).
    Returns an empty dict on any failure (best-effort enrichment).
    """
    if not settings.APOLLO_API_KEY:
        logger.warning("APOLLO_API_KEY not configured, skipping enrichment")
        return {}

    if not email and not linkedin_url:
        return {}

    payload: dict[str, Any] = {"reveal_personal_emails": True}
    if email:
        payload["email"] = email
    else:
        payload["linkedin_url"] = linkedin_url

    identifier = email or linkedin_url

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.apollo.io/api/v1/people/match",
                headers={
                    "x-api-key": settings.APOLLO_API_KEY,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        logger.warning("Apollo enrichment failed for %s", identifier, exc_info=True)
        return {}

    person = data.get("person") or {}
    if not person:
        return {}

    result: dict[str, Any] = {}

    if person.get("first_name"):
        result["given_name"] = person["first_name"]
    if person.get("last_name"):
        result["family_name"] = person["last_name"]
    if person.get("name"):
        result["full_name"] = person["name"]
    if person.get("title"):
        result["title"] = person["title"]

    org = person.get("organization") or {}
    if org.get("name"):
        result["company"] = org["name"]

    # Build location from city/state/country
    location_parts = [
        person.get("city"),
        person.get("state"),
        person.get("country"),
    ]
    location = ", ".join(p for p in location_parts if p)
    if location:
        result["location"] = location

    if person.get("linkedin_url"):
        result["linkedin_url"] = person["linkedin_url"]

    # Extract Twitter handle from URL
    twitter_url = person.get("twitter_url") or ""
    if twitter_url:
        handle = twitter_url.rstrip("/").split("/")[-1]
        if handle:
            result["twitter_handle"] = handle.lstrip("@")

    # Phone numbers
    phone_numbers = person.get("phone_numbers") or []
    phones = [
        p.get("sanitized_number")
        for p in phone_numbers
        if p.get("sanitized_number")
    ]
    if phones:
        result["phones"] = phones

    if person.get("photo_url"):
        result["avatar_url"] = person["photo_url"]

    if person.get("email"):
        result["emails"] = [person["email"]]

    return result
