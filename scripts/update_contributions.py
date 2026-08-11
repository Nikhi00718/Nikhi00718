from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

USERNAME = "Nikhi00718"
README = Path("README.md")
START = "<!-- OSS-CONTRIBUTIONS:START -->"
END = "<!-- OSS-CONTRIBUTIONS:END -->"


def github_search() -> list[dict]:
    query = f"author:{USERNAME} is:pr -user:{USERNAME}"
    url = "https://api.github.com/search/issues?" + urllib.parse.urlencode(
        {"q": query, "per_page": 100, "sort": "updated", "order": "desc"}
    )
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
            "User-Agent": f"{USERNAME}-profile",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)["items"]


def clean(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def row(item: dict) -> str:
    repository = item["repository_url"].removeprefix("https://api.github.com/repos/")
    project_url = f"https://github.com/{repository}"
    return f"| [{repository}]({project_url}) | [{clean(item['title'])}]({item['html_url']}) |"


def table(items: list[dict]) -> str:
    lines = ["| Project | Contribution |", "| --- | --- |"]
    lines.extend(row(item) for item in items)
    return "\n".join(lines)


def details(label: str, items: list[dict]) -> str:
    if not items:
        return ""
    return (
        f"<details>\n<summary><strong>{label} ({len(items)})</strong></summary>\n\n"
        f"{table(items)}\n\n</details>"
    )


def build_section(items: list[dict]) -> str:
    merged = [item for item in items if item["pull_request"].get("merged_at")]
    active = [item for item in items if item["state"] == "open"]
    closed = [
        item for item in items
        if item["state"] == "closed" and not item["pull_request"].get("merged_at")
    ]
    parts = [
        START,
        f"**{len(merged)} merged · {len(active)} active · {len(closed)} closed without merge**",
    ]
    if merged:
        parts.extend(["### Merged", table(merged)])
    if active:
        parts.append(details("Active pull requests", active))
    if closed:
        parts.append(details("Closed without merge", closed))
    parts.extend([
        f"[View complete external pull-request history](https://github.com/search?q=is%3Apr+author%3A{USERNAME}+-user%3A{USERNAME}&type=pullrequests)",
        END,
    ])
    return "\n\n".join(part for part in parts if part)


def main() -> None:
    current = README.read_text(encoding="utf-8")
    section = build_section(github_search())
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    updated, replacements = pattern.subn(section, current)
    if replacements != 1:
        raise RuntimeError("Expected exactly one contribution marker block")
    README.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()

