#!/usr/bin/env python3
"""Regenerate README.md: injects public repos ordered by stars (live star badges)."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone

USER = os.environ.get("GH_USER", "ImRevoltexee")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
TOP_N = int(os.environ.get("TOP_N", "6"))
EXCLUDE = {x.strip().lower() for x in os.environ.get("EXCLUDE", "grass,rev,3in1").split(",") if x.strip()}
README = os.environ.get("README_PATH", "README.md")

API = "https://api.github.com"


def api(path: str):
    req = urllib.request.Request(
        f"{API}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{USER}-readme-bot",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def pick_repos() -> list[dict]:
    repos: list[dict] = []
    for page in range(1, 4):
        batch = api(f"/users/{USER}/repos?per_page=100&page={page}&sort=pushed")
        if not isinstance(batch, list) or not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break

    def usable(r: dict) -> bool:
        if r.get("fork") or r.get("archived") or r.get("private"):
            return False
        name = r.get("name", "")
        if name.lower() == USER.lower():  # profile repo
            return False
        if name.lower() in EXCLUDE:
            return False
        desc = (r.get("description") or "").strip()
        if len(desc) < 20:  # placeholder / emoji-only descriptions are noise
            return False
        return True

    repos = [r for r in repos if usable(r)]
    # newest first, then stable sort by stars so ties keep recency order
    repos.sort(key=lambda r: r.get("pushed_at") or "", reverse=True)
    repos.sort(key=lambda r: -r.get("stargazers_count", 0))
    return repos[:TOP_N]


def stars_badge(repo: str) -> str:
    return (
        f"https://img.shields.io/github/stars/{USER}/{repo}"
        "?style=flat-square&label=stars&color=C6F24E&labelColor=0A0A0B"
    )


def render(repos: list[dict]) -> str:
    rows = []
    for r in repos:
        name = r["name"]
        desc = (r.get("description") or "").strip().replace("|", "\\|")
        if len(desc) > 110:
            desc = desc[:107].rstrip() + "..."
        lang = r.get("language") or "-"
        rows.append(
            f"**[{name}](https://github.com/{USER}/{name})**"
            f"<br/><sub>{desc or '—'}</sub>"
            f"<br/><sub>`{lang}`</sub> "
            f"![stars]({stars_badge(name)})"
        )

    cells = [f"<td width=\"50%\" valign=\"top\">\n\n{row}\n\n</td>" for row in rows]
    pairs = [cells[i : i + 2] for i in range(0, len(cells), 2)]
    table = "\n".join("<tr>\n" + "\n".join(p) + "\n</tr>" for p in pairs)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""<img src="assets/header.svg" width="100%" alt="Revolt" />

Backend, bots and tooling. Python · TypeScript · PHP.

## Selected work

<sub>ordered by stars, refreshed automatically — last build {stamp}</sub>

<table>
{table}
</table>

<sub>everything else: [repositories](https://github.com/{USER}?tab=repositories)</sub>

## Stack

`python` `typescript` `php` `laravel` `node` `bash` `lua` `linux` `docker` `nginx` `mysql` `sqlite` `redis` `git`

<img src="https://github-readme-streak-stats-eight.vercel.app?user={USER}&theme=github-dark&hide_border=true&background=0A0A0B00&ring=C6F24E&fire=C6F24E&currStreakLabel=C6F24E&sideLabels=9CA3AF&dates=6B7280" width="58%" alt="streak" />

## Elsewhere

<a href="https://m.youtube.com/@MrRevolt"><img src="https://img.shields.io/badge/YouTube-MrRevolt-FF0000?style=flat-square&logo=youtube&logoColor=white" alt="YouTube" /></a>
<a href="https://saweria.co/Revolt"><img src="https://img.shields.io/badge/Saweria-support-C6F24E?style=flat-square&labelColor=0A0A0B&logo=buymeacoffee&logoColor=0A0A0B" alt="Saweria" /></a>
"""


def main() -> None:
    repos = pick_repos()
    body = render(repos)
    with open(README, "w", encoding="utf-8") as fh:
        fh.write(body)
    print(f"wrote {README}: {len(repos)} repos")
    for r in repos:
        print(f"  {r['stargazers_count']:>3}★ {r['name']}")


if __name__ == "__main__":
    main()
