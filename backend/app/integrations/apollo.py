"""Apollo People Enrichment API client."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Sentinel to distinguish "no match found" from "API call failed"
NO_MATCH: dict[str, Any] = {}


class ApolloError(Exception):
    """Raised when the Apollo API call fails (not when no match is found)."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


async def enrich_person(
    email: str | None = None,
    linkedin_url: str | None = None,
) -> dict[str, Any]:
    """Call Apollo People Match API and return normalized contact fields.

    Accepts either an email or a LinkedIn URL as the lookup identifier.
    When both are provided, email takes priority (higher match quality).

    Returns:
        dict of enriched fields if a match is found.
        Empty dict (NO_MATCH) if no match in Apollo's database.

    Raises:
        ApolloError: on API key issues, rate limits, network errors, etc.
    """
    if not settings.APOLLO_API_KEY:
        raise ApolloError("APOLLO_API_KEY not configured")

    if not email and not linkedin_url:
        return NO_MATCH

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
    except httpx.TimeoutException:
        logger.warning(
            "Apollo enrichment timed out for %s",
            identifier,
            extra={"provider": "apollo", "identifier": identifier},
        )
        raise ApolloError("Apollo API request timed out", status_code=None)
    except httpx.HTTPError as exc:
        logger.warning(
            "Apollo enrichment network error for %s: %s",
            identifier,
            exc,
            extra={"provider": "apollo", "identifier": identifier},
            exc_info=True,
        )
        raise ApolloError(f"Apollo API network error: {exc}") from exc

    if resp.status_code == 401:
        logger.error(
            "Apollo API key invalid (401) for %s",
            identifier,
            extra={"provider": "apollo", "http_status": 401},
        )
        raise ApolloError("Apollo API key is invalid or expired", status_code=401)

    if resp.status_code == 429:
        logger.warning(
            "Apollo rate limit hit (429) for %s",
            identifier,
            extra={"provider": "apollo", "http_status": 429},
        )
        raise ApolloError("Apollo API rate limit exceeded — try again later", status_code=429)

    if resp.status_code >= 400:
        logger.warning(
            "Apollo API error %d for %s: %s",
            resp.status_code,
            identifier,
            resp.text[:200],
            extra={"provider": "apollo", "http_status": resp.status_code},
        )
        raise ApolloError(
            f"Apollo API returned {resp.status_code}",
            status_code=resp.status_code,
        )

    try:
        data = resp.json()
    except ValueError:
        logger.warning(
            "Apollo returned invalid JSON for %s: %s",
            identifier,
            resp.text[:200],
            extra={"provider": "apollo"},
        )
        raise ApolloError("Apollo API returned invalid JSON")

    person = data.get("person") or {}
    if not person:
        logger.info(
            "Apollo: no match found for %s",
            identifier,
            extra={"provider": "apollo", "identifier": identifier},
        )
        return NO_MATCH

    logger.info(
        "Apollo: enriched %s (fields: %s)",
        identifier,
        ", ".join(k for k in person if person[k]),
        extra={"provider": "apollo", "identifier": identifier},
    )

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
