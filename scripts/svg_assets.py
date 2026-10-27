#!/usr/bin/env python3
"""
SVG renderer for the minazliu GitHub profile.

Design system
- One neutral ink palette + a single mint accent (blue and amber as secondary).
- Sans for statements, mono for labels/metadata — reads like an engineer's notebook.
- Every section is a standalone SVG with a dark and light variant so the README
  follows the viewer's GitHub theme via <picture>.

Story sections (hero, what-i-do, fun facts, path, toolbox) live in CONTENT below —
edit the words there. The stats panel is rendered from data/repo_stats.json, which
analyze_repos.py refreshes daily through GitHub Actions.
"""
from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

W = 900  # canvas width shared by every asset

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"


@dataclass(frozen=True)
class Theme:
    name: str
    bg: str
    surface: str
    border: str
    text: str
    muted: str
    faint: str
    accent: str
    accent_soft: str
    blue: str
    blue_soft: str
    amber: str
    amber_soft: str
    pink: str
    grid: str


DARK = Theme(
    name="dark",
    bg="#0B0D10", surface="#111419", border="#242B35",
    text="#ECEFF4", muted="#9AA4B2", faint="#5F6B7A",
    accent="#3DDC97", accent_soft="#12281F",
    blue="#7AA2FF", blue_soft="#161E33",
    amber="#FFB454", amber_soft="#2A2114",
    pink="#FF7AB6",
    grid="#1A1F27",
)

LIGHT = Theme(
    name="light",
    bg="#FFFFFF", surface="#F7F8FA", border="#DDE2E8",
    text="#0F1419", muted="#525C68", faint="#8A94A1",
    accent="#0B9A63", accent_soft="#E6F5EE",
    blue="#3563D9", blue_soft="#EAF0FC",
    amber="#B86E00", amber_soft="#FBF1E1",
    pink="#C8357A",
    grid="#EEF1F4",
)

# --------------------------------------------------------------------------- #
# Story content — edit here, not in the render functions.
# --------------------------------------------------------------------------- #
CONTENT: dict[str, Any] = {
    "hero": {
        "kicker": "HELLO, WORLD — I'M MINA LIU",
        "headline": ["I build AI that ships,", "and make it make sense."],
        "sub": [
            "Engineer brain. Translator mouth. PM calendar.",
            "Sr. TPM in AI Software at Tenstorrent · Santa Clara, CA",
        ],
        # (kind, text) — "cmd" lines get a $ prompt, "out" lines are output
        "terminal": [
            ("cmd", "whoami"),
            ("out", "builder · bridge · lead"),
            ("cmd", "cat superpowers.txt"),
            ("out", "› ideas  → working demos"),
            ("out", "› jargon → plain English"),
            ("out", "› plans  → shipped code"),
            ("cmd", "./ship --today"),
            ("ok", "✓ shipped. coffee++"),
        ],
    },
    "what": [
        {
            "index": "01 / BUILD",
            "title": "I build with AI",
            "points": [
                "LLM apps, agents & RAG",
                "Evals before vibes",
                "Python, notebook → prod",
            ],
        },
        {
            "index": "02 / BRIDGE",
            "title": "I bridge tech & people",
            "points": [
                "Discovery → demo in days",
                "Architectures anyone gets",
                "APIs, integrations, POCs",
            ],
        },
        {
            "index": "03 / LEAD",
            "title": "I lead by shipping",
            "points": [
                "Roadmaps with working code",
                "Unblock teams, cut cycle time",
                "Risks spotted early, said plainly",
            ],
        },
    ],
    # (big label, line 1, line 2)
    "facts": [
        ("2020", "First repo: a COVID-19", "bar-chart race. Origin story."),
        ("×3", "Built recommenders in Python,", "R and Java. Ask me for a movie."),
        ("SILICON", "By day I help ship software", "that runs on AI chips."),
        ("08:00 UTC", "This page redraws itself", "daily. Zero humans involved."),
        ("CS221", "Binging Stanford's AI", "lectures for fun. Yes, fun."),
        ("0", "Favorite meeting: the one", "I automated away."),
    ],
    "journey": [
        ("2020", "Data nerd", ["R & Python analysis,", "viz & NLP"]),
        ("2023", "ML & cloud builder", ["Recommenders, streaming,", "microservices"]),
        ("2023 →", "Sr. TPM · AI software", ["Programs for AI chips,", "hands on keyboard"]),
        ("NOW", "Agentic AI", ["LLM agents, evals,", "human-in-the-loop"]),
    ],
    "stack": [
        ("AI & AGENTS", ["Python", "PyTorch", "Hugging Face", "LLM APIs", "Claude",
                         "LangGraph", "RAG", "Vector DBs", "Evals", "MCP"]),
        ("BUILD & SHIP", ["TypeScript", "FastAPI", "React", "Docker", "Kubernetes",
                          "AWS", "Azure", "Git"]),
        ("DATA", ["SQL", "PostgreSQL", "Pandas", "Spark", "Airflow"]),
        ("SOLUTIONS & PROGRAMS", ["Discovery", "POCs & demos", "System design",
                                  "Roadmaps", "Agile", "Exec comms"]),
    ],
}

# --------------------------------------------------------------------------- #
# Primitives
# --------------------------------------------------------------------------- #


def esc(v: Any) -> str:
    return html.escape(str(v), quote=True)


def text(x, y, value, size, color, *, weight=400, anchor="start", font=SANS,
         spacing=None, extra="") -> str:
    ls = f' letter-spacing="{spacing}"' if spacing is not None else ""
    return (
        f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" '
        f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}"{ls}{extra}>'
        f"{esc(value)}</text>"
    )


def rect(x, y, w, h, r, fill, stroke="none", sw=1, extra="") -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{extra}/>'
    )


def frame(t: Theme, h: int, uid: str, body: str, *, label: str, grid=True) -> str:
    pattern = (
        f'<pattern id="{uid}-grid" width="24" height="24" patternUnits="userSpaceOnUse">'
        f'<circle cx="1" cy="1" r="1" fill="{t.grid}"/></pattern>'
    )
    grid_fill = rect(1, 1, W - 2, h - 2, 18, f"url(#{uid}-grid)") if grid else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" '
        f'width="{W}" height="{h}" role="img" aria-label="{esc(label)}">\n'
        f"<defs>{pattern}</defs>\n"
        f"{rect(1, 1, W - 2, h - 2, 18, t.bg, t.border, 1)}\n"
        f"{grid_fill}\n{body}\n</svg>\n"
    )


def approx_width(s: str, size: float, *, mono=False, bold=False) -> float:
    if mono:
        return len(s) * size * 0.61
    per = 0.56 if bold else 0.52
    narrow = sum(1 for c in s if c in "il.,:;'|!·ftrj ")
    wide = sum(1 for c in s if c in "mwMWOQGD@")
    return (len(s) + 0.25 * wide - 0.35 * narrow) * size * per


def chip(x, y, label, t: Theme, *, fill=None, stroke=None, color=None, size=11.5,
         h=28) -> tuple[str, float]:
    w = approx_width(label, size, mono=True) + 26
    s = rect(x, y, w, h, h / 2, fill or t.surface, stroke or t.border, 1)
    s += text(x + w / 2, y + h / 2 + size * 0.36, label, size, color or t.muted,
              weight=600, anchor="middle", font=MONO)
    return s, w


def section_header(x, y, index, title, t: Theme) -> str:
    return (
        text(x, y, index, 11, t.accent, weight=700, font=MONO, spacing=1.5)
        + text(x, y + 30, title, 22, t.text, weight=700)
    )


def tones(t: Theme) -> list[tuple[str, str]]:
    return [(t.accent, t.accent_soft), (t.blue, t.blue_soft), (t.amber, t.amber_soft)]


# --------------------------------------------------------------------------- #
# Hero — headline + animated terminal
# --------------------------------------------------------------------------- #


def generate_hero(t: Theme) -> str:
    c = CONTENT["hero"]
    uid = f"hero-{t.name}"
    h = 340
    x0 = 48
    b = []

    # waving status dot + kicker
    b.append(
        f'<circle cx="{x0 + 5}" cy="62" r="5" fill="{t.accent}">'
        '<animate attributeName="opacity" values="1;.25;1" dur="2.4s" repeatCount="indefinite"/>'
        "</circle>"
    )
    b.append(text(x0 + 20, 66, c["kicker"], 12, t.muted, weight=600, font=MONO, spacing=1.6))

    line1, line2 = c["headline"]
    b.append(text(x0, 128, line1, 36, t.text, weight=800, spacing=-0.8))
    b.append(text(x0, 174, line2, 36, t.accent, weight=800, spacing=-0.8))

    b.append(text(x0, 220, c["sub"][0], 17, t.text, weight=600))
    b.append(text(x0, 248, c["sub"][1], 14, t.muted))

    # little "ships" squiggle under the headline: three dots that bounce
    for i, col in enumerate((t.accent, t.blue, t.amber)):
        cx = x0 + 6 + i * 18
        b.append(
            f'<circle cx="{cx}" cy="290" r="5" fill="{col}">'
            f'<animate attributeName="cy" values="290;282;290" dur="1.2s" begin="{i * 0.18:.2f}s" '
            'repeatCount="indefinite"/></circle>'
        )
    b.append(text(x0 + 62, 294, "currently: making agents useful", 12, t.faint, font=MONO))

    # terminal window
    tx, ty, tw, th = 588, 40, 270, 260
    b.append(rect(tx, ty, tw, th, 14, t.surface, t.border, 1))
    b.append(f'<line x1="{tx}" y1="{ty + 34}" x2="{tx + tw}" y2="{ty + 34}" stroke="{t.border}"/>')
    for i, col in enumerate(("#FF5F57", "#FEBC2E", "#28C840")):
        b.append(f'<circle cx="{tx + 20 + i * 16}" cy="{ty + 17}" r="5" fill="{col}"/>')
    b.append(text(tx + tw / 2 + 20, ty + 21, "~/mina", 11, t.faint, anchor="middle", font=MONO))

    lines = c["terminal"]
    dur = 10.0
    step = 0.7
    for i, (kind, value) in enumerate(lines):
        ly = ty + 62 + i * 24
        start = (0.4 + i * step) / dur
        key = f"0;{start:.3f};{start + 0.02:.3f};0.93;1"
        anim = (f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="{key}" '
                f'dur="{dur}s" repeatCount="indefinite"/>')
        if kind == "cmd":
            body = (text(tx + 18, ly, "$", 12, t.accent, weight=700, font=MONO)
                    + text(tx + 32, ly, value, 12, t.text, weight=600, font=MONO))
        elif kind == "ok":
            body = text(tx + 18, ly, value, 12, t.accent, weight=700, font=MONO)
        else:
            body = text(tx + 18, ly, value, 12, t.muted, font=MONO)
        b.append(f"<g opacity='0'>{anim}{body}</g>")
    # blinking cursor after last line
    cy = ty + 62 + (len(lines) - 1) * 24 - 10
    cx = tx + 18 + approx_width(lines[-1][1], 12, mono=True) + 6
    b.append(
        f'<rect x="{cx:.0f}" y="{cy}" width="7" height="13" fill="{t.accent}">'
        '<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect>'
    )

    return frame(t, h, uid, "\n".join(b),
                 label="Mina Liu — I build AI that ships, and make it make sense.")


# --------------------------------------------------------------------------- #
# What I do — build / bridge / lead
# --------------------------------------------------------------------------- #


def generate_what(t: Theme) -> str:
    uid = f"what-{t.name}"
    h = 272
    b = [section_header(48, 56, "WHAT I DO", "Build it. Explain it. Ship it.", t)]
    col_w, gap, x0, y0 = 256, 18, 48, 110
    for i, item in enumerate(CONTENT["what"]):
        x = x0 + i * (col_w + gap)
        tone, _ = tones(t)[i]
        b.append(rect(x, y0, col_w, 132, 14, t.surface, t.border, 1))
        b.append(rect(x + 20, y0 + 16, 22, 3, 1.5, tone))
        b.append(text(x + 20, y0 + 34, item["index"], 10.5, tone, weight=700, font=MONO, spacing=1.4))
        b.append(text(x + 20, y0 + 58, item["title"], 17, t.text, weight=700))
        for j, p in enumerate(item["points"]):
            yy = y0 + 84 + j * 18
            b.append(text(x + 20, yy, "›", 13, tone, weight=700, font=MONO))
            b.append(text(x + 34, yy, p, 12.5, t.muted))
    return frame(t, h, uid, "\n".join(b), label="What I do: build with AI, translate tech and people, lead by shipping")


# --------------------------------------------------------------------------- #
# Fun facts
# --------------------------------------------------------------------------- #


def generate_facts(t: Theme) -> str:
    uid = f"facts-{t.name}"
    facts = CONTENT["facts"]
    cols, col_w, row_h, gap = 3, 256, 112, 18
    rows = (len(facts) + cols - 1) // cols
    h = 110 + rows * row_h + (rows - 1) * gap + 34
    b = [section_header(48, 56, "FUN FACTS", "Things you won't find on my resume", t)]
    palette = tones(t)
    for i, (big, l1, l2) in enumerate(facts):
        r, c = divmod(i, cols)
        x = 48 + c * (col_w + gap)
        y = 110 + r * (row_h + gap)
        tone, soft = palette[i % 3]
        b.append(rect(x, y, col_w, row_h, 14, t.surface, t.border, 1))
        # floating badge
        bw = approx_width(big, 15, mono=True) + 22
        b.append(
            f'<g><animateTransform attributeName="transform" type="translate" '
            f'values="0 0;0 -3;0 0" dur="3s" begin="{i * 0.35:.2f}s" repeatCount="indefinite"/>'
            f'{rect(x + 18, y + 18, bw, 30, 8, soft, tone, 1)}'
            f'{text(x + 18 + bw / 2, y + 38, big, 15, tone, weight=800, anchor="middle", font=MONO)}'
            "</g>"
        )
        b.append(text(x + 18, y + 74, l1, 13, t.text, weight=500))
        b.append(text(x + 18, y + 94, l2, 13, t.muted))
    return frame(t, h, uid, "\n".join(b), label="Fun facts about Mina")


# --------------------------------------------------------------------------- #
# Journey timeline
# --------------------------------------------------------------------------- #


def generate_journey(t: Theme) -> str:
    uid = f"journey-{t.name}"
    h = 250
    b = [section_header(48, 56, "THE PATH", "From data nerd to agent builder", t)]
    steps = CONTENT["journey"]
    x0, x1, ly = 64, W - 64, 128
    b.append(f'<line x1="{x0}" y1="{ly}" x2="{x1}" y2="{ly}" stroke="{t.border}" stroke-width="2"/>')
    span = x1 - x0
    b.append(
        f'<line x1="{x0}" y1="{ly}" x2="{x1}" y2="{ly}" stroke="{t.accent}" stroke-width="2" '
        f'stroke-dasharray="{span}" stroke-dashoffset="0">'
        f'<animate attributeName="stroke-dashoffset" values="{span};0;0" keyTimes="0;.4;1" '
        'dur="6s" repeatCount="indefinite"/></line>'
    )
    step = span / (len(steps) - 1)
    for i, (year, title, lines) in enumerate(steps):
        x = x0 + i * step
        last = i == len(steps) - 1
        anchor = "start" if i == 0 else ("end" if last else "middle")
        if last:
            b.append(
                f'<circle cx="{x}" cy="{ly}" r="11" fill="{t.accent_soft}">'
                '<animate attributeName="r" values="8;14;8" dur="2.4s" repeatCount="indefinite"/></circle>'
            )
        b.append(
            f'<circle cx="{x}" cy="{ly}" r="6" fill="{t.accent if last else t.bg}" '
            f'stroke="{t.accent}" stroke-width="2"/>'
        )
        tx = x - 6 if i == 0 else (x + 6 if last else x)
        b.append(text(tx, ly - 20, year, 11, t.accent if last else t.faint, weight=700, font=MONO,
                      spacing=1.2, anchor=anchor))
        b.append(text(tx, ly + 34, title, 15, t.text, weight=700, anchor=anchor))
        for j, ln in enumerate(lines):
            b.append(text(tx, ly + 56 + j * 18, ln, 12.5, t.muted, anchor=anchor))
    return frame(t, h, uid, "\n".join(b), label="Path: data nerd, ML and cloud builder, TPM in AI software, agentic AI")


# --------------------------------------------------------------------------- #
# Toolbox
# --------------------------------------------------------------------------- #


def generate_stack(t: Theme) -> str:
    uid = f"stack-{t.name}"
    label_x, chips_x, right = 48, 248, W - 48
    y = 110
    b = []
    palette = tones(t) + [(t.pink, t.surface)]
    for gi, (group, items) in enumerate(CONTENT["stack"]):
        tone, soft = palette[gi % len(palette)]
        b.append(text(label_x, y + 18, group, 10.5, tone, weight=700, font=MONO, spacing=1.3))
        x = chips_x
        for j, item in enumerate(items):
            w = approx_width(item, 11.5, mono=True) + 26
            if x + w > right:
                x = chips_x
                y += 36
            s, w = chip(x, y, item, t, fill=soft if j == 0 else t.surface,
                        stroke=tone if j == 0 else t.border,
                        color=tone if j == 0 else t.text)
            b.append(s)
            x += w + 8
        y += 36 + 16
        if gi < len(CONTENT["stack"]) - 1:
            b.append(f'<line x1="{label_x}" y1="{y - 8}" x2="{right}" y2="{y - 8}" '
                     f'stroke="{t.border}" stroke-dasharray="2 4"/>')
            y += 6
    h = int(y + 18)
    head = section_header(48, 56, "TOOLBOX", "What I reach for", t)
    return frame(t, h, uid, head + "\n" + "\n".join(b), label="Tech stack and toolbox")


# --------------------------------------------------------------------------- #
# Live stats (data-driven)
# --------------------------------------------------------------------------- #

LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#F1E05A", "TypeScript": "#3178C6",
    "Java": "#B07219", "CSS": "#663399", "HTML": "#E34C26", "R": "#198CE7",
}


def fmt(v: Any) -> str:
    return "—" if v is None else str(v)


def generate_stats(data: dict[str, Any], t: Theme) -> str:
    uid = f"stats-{t.name}"
    h = 262
    b = [section_header(48, 56, "LIVE  ·  REFRESHED DAILY", "Keyboard telemetry", t)]

    contrib = data.get("contributions", {}) or {}
    metrics = [
        (fmt(contrib.get("commits")), "commits · 12 mo"),
        (fmt(contrib.get("longest_streak")), "longest streak · days"),
        (fmt(data.get("language_count")), "languages spoken"),
        ("1", "profile that codes itself"),
    ]
    mx, my, mw, mg = 48, 104, 190, 13
    for i, (v, label) in enumerate(metrics):
        x = mx + i * (mw + mg)
        b.append(rect(x, my, mw, 76, 12, t.surface, t.border, 1))
        b.append(text(x + 18, my + 40, v, 30, t.text, weight=800, spacing=-0.6))
        b.append(text(x + 18, my + 62, label, 11, t.faint, weight=600, font=MONO))

    by = 210
    b.append(text(48, by + 18, "SPEAKS", 10.5, t.faint, weight=700, font=MONO, spacing=1.4))
    lx = 120
    for i, lang in enumerate(data.get("language_distribution", [])[:7]):
        name = lang["name"]
        w = approx_width(name, 11.5, mono=True) + 34
        if lx + w > W - 48:
            break
        b.append(rect(lx, by, w, 28, 14, t.surface, t.border, 1))
        b.append(f'<circle cx="{lx + 14}" cy="{by + 14}" r="4" fill="{LANG_COLORS.get(name, t.faint)}"/>')
        b.append(text(lx + 24, by + 18, name, 11.5, t.text if i == 0 else t.muted, weight=600, font=MONO))
        lx += w + 8

    gen = data.get("generated_at", "")[:10]
    b.append(text(W - 48, 56, f"updated {gen}", 11, t.faint, anchor="end", font=MONO))
    return frame(t, h, uid, "\n".join(b), label="Live GitHub stats")


# --------------------------------------------------------------------------- #
# Entry point (called by analyze_repos.py)
# --------------------------------------------------------------------------- #


def generate_all_assets(data: dict[str, Any], assets_dir: Path) -> None:
    assets_dir = Path(assets_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)
    for t in (DARK, LIGHT):
        out = {
            f"hero_{t.name}.svg": generate_hero(t),
            f"what_{t.name}.svg": generate_what(t),
            f"facts_{t.name}.svg": generate_facts(t),
            f"journey_{t.name}.svg": generate_journey(t),
            f"stack_{t.name}.svg": generate_stack(t),
            f"stats_{t.name}.svg": generate_stats(data, t),
        }
        for name, svg in out.items():
            (assets_dir / name).write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    # Local preview without hitting the API: python3 scripts/svg_assets.py
    import json

    root = Path(__file__).resolve().parent.parent
    payload = json.loads((root / "data/repo_stats.json").read_text(encoding="utf-8"))
    generate_all_assets(payload, root / "assets")
    print("Rendered assets from cached data/repo_stats.json")
