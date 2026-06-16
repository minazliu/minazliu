#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from svg_assets import generate_all_assets

USERNAME = "Mina314"
API = "https://api.github.com"
GRAPHQL = "https://api.github.com/graphql"
ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data/repo_stats.json"
ASSETS_DIR = ROOT / "assets"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def build_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    token = os.getenv("GITHUB_TOKEN")
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
    else:
        log.warning("GITHUB_TOKEN is not set; contribution stats will show N/A.")
    return s


def fetch_repositories(s: requests.Session) -> list[dict[str, Any]]:
    repos = []
    page = 1
    while True:
        r = s.get(
            f"{API}/users/{USERNAME}/repos",
            params={"type": "owner", "sort": "updated", "per_page": 100, "page": page},
            timeout=30,
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return [r for r in repos if not r.get("fork") and not r.get("archived")]


def fetch_languages(s: requests.Session, name: str) -> dict[str, int]:
    r = s.get(f"{API}/repos/{USERNAME}/{name}/languages", timeout=30)
    if r.status_code == 404:
        return {}
    r.raise_for_status()
    return r.json()


def fetch_contributions(s: requests.Session) -> dict[str, Any]:
    if "Authorization" not in s.headers:
        return {"commits": None, "longest_streak": None}

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=365)
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          contributionCalendar {
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """
    r = s.post(
        GRAPHQL,
        json={
            "query": query,
            "variables": {"login": USERNAME, "from": start.isoformat(), "to": end.isoformat()},
        },
        timeout=30,
    )
    r.raise_for_status()
    payload = r.json()
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])

    collection = payload["data"]["user"]["contributionsCollection"]
    days = [
        d
        for week in collection["contributionCalendar"]["weeks"]
        for d in week["contributionDays"]
    ]

    longest = 0
    current = 0
    for day in sorted(days, key=lambda x: x["date"]):
        if day["contributionCount"] > 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    return {
        "commits": collection["totalCommitContributions"],
        "longest_streak": longest,
    }

def fetch_activity(s: requests.Session) -> list[dict[str, str]]:
    response = s.get(
        f"{API}/users/{USERNAME}/events/public",
        params={"per_page": 100},
        timeout=30,
    )
    response.raise_for_status()

    items: list[dict[str, str]] = []
    seen_keys: set[str] = set()

    for event in response.json():
        event_type = event.get("type", "")
        repo = event.get("repo", {}).get("name", "").replace(
            f"{USERNAME}/",
            "",
        )
        payload = event.get("payload", {})
        created_at = event.get("created_at", "")

        action = ""
        detail = ""
        dedupe_key = ""

        if event_type == "PushEvent":
            # Keep only the most recent push for each repository.
            dedupe_key = f"push:{repo}"

            count = payload.get("distinct_size")
            if count is None:
                count = payload.get("size")

            action = f"Updated {repo}"

            if isinstance(count, int) and count > 0:
                detail = f"{count} commit{'s' if count != 1 else ''} pushed"
            else:
                detail = "Repository updated"

        elif event_type == "PullRequestEvent":
            pull_request = payload.get("pull_request", {})
            action_name = payload.get("action", "updated").capitalize()

            dedupe_key = (
                f"pr:{repo}:"
                f"{pull_request.get('number', event.get('id', ''))}"
            )

            action = f"{action_name} pull request in {repo}"
            detail = pull_request.get("title", "")

        elif event_type == "IssuesEvent":
            issue = payload.get("issue", {})
            action_name = payload.get("action", "updated").capitalize()

            dedupe_key = (
                f"issue:{repo}:"
                f"{issue.get('number', event.get('id', ''))}"
            )

            action = f"{action_name} issue in {repo}"
            detail = issue.get("title", "")

        elif event_type == "ReleaseEvent":
            release = payload.get("release", {})

            dedupe_key = (
                f"release:{repo}:"
                f"{release.get('tag_name', event.get('id', ''))}"
            )

            action = f"Released {release.get('tag_name', '')} in {repo}"
            detail = release.get("name") or "New release published"

        elif event_type == "CreateEvent":
            ref_type = payload.get("ref_type", "item")
            ref = payload.get("ref") or ""

            dedupe_key = f"create:{repo}:{ref_type}:{ref}"

            action = f"Created {ref_type} in {repo}"
            detail = ref

        elif event_type == "ForkEvent":
            dedupe_key = f"fork:{repo}"
            action = f"Forked {repo}"
            detail = "Created a repository fork"

        elif event_type == "WatchEvent":
            dedupe_key = f"star:{repo}"
            action = f"Starred {repo}"
            detail = "Added repository to starred projects"

        else:
            continue

        if dedupe_key in seen_keys:
            continue

        seen_keys.add(dedupe_key)

        items.append(
            {
                "action": action,
                "detail": detail[:90],
                "created_at": created_at,
            }
        )

        if len(items) >= 5:
            break

    return items

def main() -> None:
    s = build_session()
    repos = fetch_repositories(s)

    language_totals: dict[str, int] = {}
    normalized = []

    for repo in repos:
        languages = fetch_languages(s, repo["name"])
        for language, amount in languages.items():
            language_totals[language] = language_totals.get(language, 0) + amount
        normalized.append({
            "name": repo["name"],
            "url": repo["html_url"],
            "description": repo.get("description"),
            "languages": languages,
            "pushed_at": repo.get("pushed_at"),
        })

    top_language = max(language_totals, key=language_totals.get) if language_totals else "N/A"
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "username": USERNAME,
        "repo_count": len(repos),
        "top_language": top_language,
        "repositories": normalized,
        "contributions": fetch_contributions(s),
        "activity": fetch_activity(s),
    }

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    generate_all_assets(data, ASSETS_DIR)
    log.info("Updated profile assets.")


if __name__ == "__main__":
    main()
