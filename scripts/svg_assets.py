"""
Native SVG asset generation for the Mina314 GitHub profile dashboard.

Generates dark and light theme variants without Matplotlib or external assets.
"""

from __future__ import annotations

import html
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

FONT = "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif"

MARKUP_LANGUAGES = {"HTML", "CSS", "JSON", "YAML", "Markdown", "XML", "SVG"}


@dataclass(frozen=True)
class Theme:
    """Color tokens for a dashboard theme variant."""

    name: str
    bg_start: str
    bg_end: str
    card: str
    card_inner: str
    border: str
    border_accent: str
    text_primary: str
    text_secondary: str
    text_muted: str
    accent_blue: str
    accent_violet: str
    accent_cyan: str
    track: str
    glow_blue: str
    glow_violet: str
    chip_bg: str
    status_dev: str
    status_live: str
    status_concept: str


DARK = Theme(
    name="dark",
    bg_start="#0d1117",
    bg_end="#161b22",
    card="#161b22",
    card_inner="#1c2128",
    border="#30363d",
    border_accent="#6366f1",
    text_primary="#e6edf3",
    text_secondary="#8b949e",
    text_muted="#6e7681",
    accent_blue="#58a6ff",
    accent_violet="#a371f7",
    accent_cyan="#56d4dd",
    track="#30363d",
    glow_blue="rgba(88,166,255,0.12)",
    glow_violet="rgba(163,113,247,0.10)",
    chip_bg="#21262d",
    status_dev="#58a6ff",
    status_live="#3fb950",
    status_concept="#a371f7",
)

LIGHT = Theme(
    name="light",
    bg_start="#ffffff",
    bg_end="#f6f8fa",
    card="#ffffff",
    card_inner="#f6f8fa",
    border="#d0d7de",
    border_accent="#8250df",
    text_primary="#1f2328",
    text_secondary="#656d76",
    text_muted="#8c959f",
    accent_blue="#0969da",
    accent_violet="#8250df",
    accent_cyan="#0969da",
    track="#eaeef2",
    glow_blue="rgba(9,105,218,0.06)",
    glow_violet="rgba(130,80,223,0.06)",
    chip_bg="#f6f8fa",
    status_dev="#0969da",
    status_live="#1a7f37",
    status_concept="#8250df",
)


def _esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def _svg_open(width: int, height: int, defs: str, body: str) -> str:
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
        f"<defs>{defs}</defs>\n{body}\n</svg>"
    )


def _grad_defs(theme: Theme, uid: str) -> str:
    return f"""
    <linearGradient id="{uid}_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{theme.bg_start}"/>
      <stop offset="100%" stop-color="{theme.bg_end}"/>
    </linearGradient>
    <linearGradient id="{uid}_accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{theme.accent_blue}"/>
      <stop offset="100%" stop-color="{theme.accent_violet}"/>
    </linearGradient>
    <radialGradient id="{uid}_glow" cx="75%" cy="40%" r="45%">
      <stop offset="0%" stop-color="{theme.glow_blue}"/>
      <stop offset="100%" stop-color="transparent"/>
    </radialGradient>
    """


def _rect(x: float, y: float, w: float, h: float, rx: float, fill: str, stroke: str = "none", sw: float = 1) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
    )


def _text(
    x: float,
    y: float,
    content: str,
    size: int = 14,
    fill: str = "#fff",
    weight: str = "normal",
    anchor: str = "start",
) -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">'
        f"{_esc(content)}</text>"
    )


def _pill(x: float, y: float, label: str, theme: Theme, uid: str, idx: int) -> str:
    w = len(label) * 8 + 36
    return (
        f'{_rect(x, y, w, 32, 16, theme.chip_bg, theme.border, 1)}'
        f'{_text(x + 16, y + 21, label, 13, theme.text_secondary)}'
    )


def _chip(x: float, y: float, label: str, theme: Theme) -> str:
    w = max(len(label) * 7 + 24, 48)
    return (
        f'{_rect(x, y, w, 26, 13, theme.chip_bg, theme.border, 1)}'
        f'{_text(x + 12, y + 18, label, 12, theme.text_muted)}'
    )


def _icon_nodes(cx: float, cy: float, color: str) -> str:
    return f"""
    <circle cx="{cx}" cy="{cy}" r="10" fill="none" stroke="{color}" stroke-width="1.5"/>
    <circle cx="{cx-18}" cy="{cy+14}" r="6" fill="none" stroke="{color}" stroke-width="1.2"/>
    <circle cx="{cx+18}" cy="{cy+14}" r="6" fill="none" stroke="{color}" stroke-width="1.2"/>
    <line x1="{cx}" y1="{cy+10}" x2="{cx-18}" y2="{cy+8}" stroke="{color}" stroke-width="1"/>
    <line x1="{cx}" y1="{cy+10}" x2="{cx+18}" y2="{cy+8}" stroke="{color}" stroke-width="1"/>
    """


def _icon_gear(cx: float, cy: float, color: str) -> str:
    return f"""
    <circle cx="{cx}" cy="{cy}" r="8" fill="none" stroke="{color}" stroke-width="1.5"/>
    <circle cx="{cx}" cy="{cy}" r="3" fill="{color}"/>
    <path d="M{cx} {cy-14}v4 M{cx} {cy+10}v4 M{cx-14} {cy}h4 M{cx+10} {cy}h4" stroke="{color}" stroke-width="1.5"/>
    """


def _icon_signal(cx: float, cy: float, color: str) -> str:
    return f"""
    <rect x="{cx-16}" y="{cy+4}" width="6" height="12" rx="2" fill="{color}" opacity="0.5"/>
    <rect x="{cx-6}" y="{cy-2}" width="6" height="18" rx="2" fill="{color}" opacity="0.7"/>
    <rect x="{cx+4}" y="{cy-10}" width="6" height="26" rx="2" fill="{color}"/>
    """


def _hero_illustration(theme: Theme, uid: str) -> str:
    x0, y0 = 820, 60
    blocks = [
        (x0 + 40, y0 + 180, 220, 36, theme.accent_violet, 0.35),
        (x0 + 70, y0 + 130, 220, 36, theme.accent_blue, 0.45),
        (x0 + 100, y0 + 80, 220, 36, theme.accent_cyan, 0.55),
    ]
    parts = []
    for bx, by, bw, bh, color, op in blocks:
        parts.append(
            f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="10" '
            f'fill="{color}" opacity="{op}" stroke="{theme.border}" stroke-width="1"/>'
        )
    nodes = [
        (x0 + 60, y0 + 250, theme.accent_blue),
        (x0 + 180, y0 + 260, theme.accent_violet),
        (x0 + 300, y0 + 240, theme.accent_cyan),
        (x0 + 340, y0 + 120, theme.accent_blue),
    ]
    for i, (nx, ny, nc) in enumerate(nodes):
        parts.append(f'<circle cx="{nx}" cy="{ny}" r="7" fill="{nc}" opacity="0.85"/>')
        if i < len(nodes) - 1:
            nx2, ny2, _ = nodes[i + 1]
            parts.append(
                f'<line x1="{nx}" y1="{ny}" x2="{nx2}" y2="{ny2}" '
                f'stroke="{theme.border_accent}" stroke-width="1" opacity="0.5"/>'
            )
    # faint background nodes
    for nx, ny in [(900, 100), (1050, 280), (760, 160), (1120, 200)]:
        parts.append(f'<circle cx="{nx}" cy="{ny}" r="3" fill="{theme.text_muted}" opacity="0.25"/>')
    # small labels on blocks
    parts.append(_text(x0 + 155, y0 + 103, "AI", 12, theme.text_primary, "bold", "middle"))
    parts.append(_text(x0 + 155, y0 + 153, "API", 12, theme.text_primary, "bold", "middle"))
    parts.append(_text(x0 + 145, y0 + 203, "Workflow", 12, theme.text_primary, "bold", "middle"))
    return "\n".join(parts)


def generate_profile_hero(theme: Theme) -> str:
    uid = f"hero_{theme.name}"
    defs = _grad_defs(theme, uid)
    body_parts = [
        _rect(20, 20, 1360, 380, 24, f"url(#{uid}_bg)", theme.border_accent, 1.2),
        f'<rect x="20" y="20" width="1360" height="380" rx="24" fill="url(#{uid}_glow)"/>',
        _text(72, 108, "Hi, I'm ", 32, theme.text_primary),
        f'<text x="210" y="108" font-family="{FONT}" font-size="32" font-weight="bold" fill="url(#{uid}_accent)">Mina.</text>',
        _text(72, 168, "I build agentic workflows and", 22, theme.text_secondary),
        _text(72, 202, "AI-powered operational systems.", 22, theme.text_primary, "bold"),
        _text(72, 254, "Connecting AI, APIs, automation, data, and human review", 15, theme.text_muted),
        _text(72, 278, "to make engineering execution clearer and faster.", 15, theme.text_muted),
    ]
    pills = ["Agentic Systems", "Workflow Automation", "Operational Intelligence", "Human-in-the-loop"]
    px = 72
    py = 310
    for label in pills:
        body_parts.append(_pill(px, py, label, theme, uid, 0))
        px += len(label) * 8 + 48
    body_parts.append(_hero_illustration(theme, uid))
    return _svg_open(1400, 420, defs, "\n".join(body_parts))


def generate_focus_areas(theme: Theme) -> str:
    uid = f"focus_{theme.name}"
    defs = _grad_defs(theme, uid)
    cards = [
        ("Agentic Workflows", "AI-assisted triage, classification,\nscoring, routing, and review.", _icon_nodes),
        ("Automation Systems", "APIs and orchestration across GitHub,\nJira, Slack, n8n, and internal tools.", _icon_gear),
        ("Operational Intelligence", "Signals for risks, ownership, incidents,\nSLAs, and execution health.", _icon_signal),
    ]
    body = [
        _rect(20, 20, 1360, 260, 20, f"url(#{uid}_bg)", theme.border, 1),
        _text(56, 58, "Focus Areas", 22, theme.text_primary, "bold"),
    ]
    cw = 400
    gap = 40
    for i, (title, desc, icon_fn) in enumerate(cards):
        x = 56 + i * (cw + gap)
        y = 80
        body.append(_rect(x, y, cw, 180, 16, theme.card_inner, theme.border, 1))
        body.append(icon_fn(x + 36, y + 36, theme.accent_blue))
        body.append(_text(x + 68, y + 42, title, 16, theme.text_primary, "bold"))
        for j, line in enumerate(desc.split("\n")):
            body.append(_text(x + 24, y + 78 + j * 22, line, 14, theme.text_secondary))
    return _svg_open(1400, 300, defs, "\n".join(body))


SELECTED_PROJECTS = [
    {
        "title": "Agentic Issue Triage",
        "status": "In development",
        "status_color_key": "status_dev",
        "description": "AI-assisted GitHub issue analysis with classification, risk scoring, routing, and human review.",
        "tags": ["Python", "GitHub API", "LLM", "Human-in-the-loop"],
    },
    {
        "title": "GitHub Portfolio Intelligence",
        "status": "Live",
        "status_color_key": "status_live",
        "description": "A self-updating repository analysis pipeline that generates profile insights using the GitHub API.",
        "tags": ["Python", "Pandas", "GitHub Actions", "SVG"],
    },
    {
        "title": "Workflow Patterns",
        "status": "Concept",
        "status_color_key": "status_concept",
        "description": "Reusable architectures for intake, classification, approval, routing, and escalation.",
        "tags": ["Workflow Design", "AI Agents", "APIs", "System Design"],
    },
]


def generate_selected_projects(theme: Theme) -> str:
    uid = f"proj_{theme.name}"
    defs = _grad_defs(theme, uid)
    body = [
        _rect(20, 20, 1360, 390, 20, f"url(#{uid}_bg)", theme.border, 1),
        _text(56, 58, "Selected Projects", 22, theme.text_primary, "bold"),
    ]
    cw = 400
    gap = 40
    for i, proj in enumerate(SELECTED_PROJECTS):
        x = 56 + i * (cw + gap)
        y = 80
        status_color = getattr(theme, proj["status_color_key"])
        body.append(_rect(x, y, cw, 300, 16, theme.card_inner, theme.border, 1))
        body.append(_rect(x + 24, y + 24, 40, 40, 10, theme.chip_bg, theme.border, 1))
        body.append(_icon_nodes(x + 44, y + 44, theme.accent_violet))
        body.append(_text(x + 76, y + 40, proj["title"], 16, theme.text_primary, "bold"))
        sw = len(proj["status"]) * 7 + 28
        body.append(_rect(x + 76, y + 52, sw, 22, 11, theme.chip_bg, status_color, 1.5))
        body.append(_text(x + 88, y + 68, proj["status"], 11, status_color, "bold"))
        desc_lines = _wrap_text(proj["description"], 42)
        for j, line in enumerate(desc_lines):
            body.append(_text(x + 24, y + 110 + j * 20, line, 14, theme.text_secondary))
        tx = x + 24
        ty = y + 240
        for tag in proj["tags"]:
            body.append(_chip(tx, ty, tag, theme))
            tx += max(len(tag) * 7 + 32, 56)
            if tx > x + cw - 80:
                tx = x + 24
                ty += 34
    return _svg_open(1400, 430, defs, "\n".join(body))


def _wrap_text(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        test = " ".join(current + [word])
        if len(test) <= width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _sparkline(points: Sequence[tuple[float, float]], color: str, fill: str) -> str:
    if len(points) < 2:
        return ""
    path = f"M {points[0][0]} {points[0][1]}"
    for x, y in points[1:]:
        path += f" L {x} {y}"
    area = path + f" L {points[-1][0]} {points[-1][1] + 40} L {points[0][0]} {points[0][1] + 40} Z"
    return (
        f'<path d="{area}" fill="{fill}" opacity="0.15"/>'
        f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round"/>'
    )


def _progress_bar(x: float, y: float, w: float, fraction: float, theme: Theme, label: str, pct_label: str) -> str:
    fw = max(w * min(max(fraction, 0), 1), 2)
    return (
        f'{_text(x, y, label, 13, theme.text_primary)}'
        f'{_rect(x + 180, y - 12, w, 10, 5, theme.track)}'
        f'{_rect(x + 180, y - 12, fw, 10, 5, theme.accent_blue)}'
        f'{_text(x + 180 + w + 12, y - 2, pct_label, 12, theme.text_muted)}'
    )


def _top_languages(top_languages: dict[str, int], max_items: int = 5) -> list[tuple[str, float]]:
    filtered = {
        lang: b for lang, b in top_languages.items()
        if lang not in MARKUP_LANGUAGES or len(top_languages) == 1
    }
    use = filtered or top_languages
    total = sum(use.values()) or 1
    ranked = sorted(use.items(), key=lambda x: x[1], reverse=True)[:max_items]
    return [(lang, 100.0 * b / total) for lang, b in ranked]


def generate_portfolio_insights(data: dict[str, Any], theme: Theme) -> str:
    uid = f"insights_{theme.name}"
    defs = _grad_defs(theme, uid)
    summary = data.get("summary", {})
    repo_count = data.get("repo_count", 0)
    recent = summary.get("most_recently_updated", {})
    recent_name = recent.get("name", "N/A")
    recent_date = (recent.get("pushed_at") or "")[:10]

    body = [
        _rect(20, 20, 1360, 460, 20, f"url(#{uid}_bg)", theme.border, 1),
        _text(56, 58, "Portfolio Insights", 22, theme.text_primary, "bold"),
        _text(56, 82, "Generated from public repository metadata.", 12, theme.text_muted),
    ]

    # KPI row
    kpis = [
        ("Active Repositories", str(repo_count)),
        ("Most Recently Updated", recent_name[:22]),
        ("Last Push", recent_date or "N/A"),
    ]
    for i, (label, value) in enumerate(kpis):
        kx = 56 + i * 430
        body.append(_rect(kx, 100, 390, 90, 14, theme.card_inner, theme.border, 1))
        body.append(_text(kx + 24, 132, label, 13, theme.text_muted))
        body.append(_text(kx + 24, 168, value, 22, theme.text_primary, "bold"))

    # Project focus bars
    body.append(_text(56, 222, "Project Focus", 15, theme.text_primary, "bold"))
    categories = summary.get("category_counts", {})
    cat_order = [
        "Agentic AI Workflows", "Automation & APIs", "Data & Analytics",
        "Developer Tools", "Web Applications", "Learning & Experiments", "Other",
    ]
    ranked_cats = sorted(
        ((c, categories.get(c, 0)) for c in cat_order),
        key=lambda x: x[1], reverse=True,
    )
    ranked_cats = [(c, v) for c, v in ranked_cats if v > 0][:5]
    total_cats = sum(v for _, v in ranked_cats) or 1
    short = {
        "Agentic AI Workflows": "Agentic AI",
        "Automation & APIs": "Automation",
        "Data & Analytics": "Data & Analytics",
        "Developer Tools": "Dev Tools",
        "Web Applications": "Web Apps",
        "Learning & Experiments": "Learning",
        "Other": "Other",
    }
    for i, (cat, count) in enumerate(ranked_cats):
        pct = 100.0 * count / total_cats
        body.append(_progress_bar(
            56, 248 + i * 28, 520, pct / 100.0, theme,
            short.get(cat, cat), f"{pct:.0f}% ({count})",
        ))

    # Technology mix segmented bar
    body.append(_text(720, 222, "Technology Mix", 15, theme.text_primary, "bold"))
    caps = summary.get("capability_counts", {})
    cap_order = ["AI and agents", "Automation and APIs", "Data and analytics", "Infrastructure", "Developer tooling"]
    cap_items = [(c, caps.get(c, 0)) for c in cap_order if caps.get(c, 0) > 0]
    cap_total = sum(v for _, v in cap_items) or 1
    cx = 720
    colors = [theme.accent_blue, theme.accent_violet, theme.accent_cyan, theme.accent_blue, theme.accent_violet]
    for i, (cap, count) in enumerate(cap_items):
        seg_w = 560 * count / cap_total
        body.append(_rect(cx, 248, seg_w, 14, 4, colors[i % len(colors)]))
        cx += seg_w
    for i, (cap, count) in enumerate(cap_items):
        pct = 100.0 * count / cap_total
        body.append(_text(720, 282 + i * 20, f"{cap}  ·  {pct:.0f}% ({count})", 12, theme.text_secondary))

    # Languages
    body.append(_text(56, 400, "Languages Detected", 15, theme.text_primary, "bold"))
    langs = _top_languages(summary.get("top_languages", {}))
    lx = 56
    for lang, pct in langs:
        label = f"{lang} {pct:.0f}%"
        body.append(_chip(lx, 420, label, theme))
        lx += max(len(label) * 7 + 28, 80)

    # Sparkline
    body.append(_text(720, 400, "Repository update activity", 15, theme.text_primary, "bold"))
    activity = summary.get("monthly_activity", [])
    counts = [p.get("count", 0) for p in activity]
    labels = [p.get("label", "") for p in activity]
    if counts:
        max_c = max(counts) or 1
        plot_w, plot_h = 560, 50
        px0, py0 = 720, 430
        pts = [
            (px0 + plot_w * i / max(len(counts) - 1, 1), py0 + plot_h - plot_h * c / max_c)
            for i, c in enumerate(counts)
        ]
        body.append(_sparkline(pts, theme.accent_blue, theme.accent_blue))
        if labels:
            body.append(_text(px0, py0 + plot_h + 18, labels[0], 11, theme.text_muted))
            body.append(_text(px0 + plot_w, py0 + plot_h + 18, labels[-1], 11, theme.text_muted, anchor="end"))

    return _svg_open(1400, 500, defs, "\n".join(body))


LEGACY_ASSETS = [
    "project_focus.svg",
    "technology_mix.svg",
    "impact_summary.svg",
    "portfolio_summary.svg",
    "language_distribution.svg",
    "repo_maturity.svg",
    "repository_activity.svg",
]


def generate_all_assets(data: dict[str, Any], assets_dir: Path) -> None:
    """Generate all dashboard SVG assets in dark and light themes."""
    assets_dir.mkdir(parents=True, exist_ok=True)

    static_generators = [
        ("profile_hero", generate_profile_hero),
        ("focus_areas", generate_focus_areas),
        ("selected_projects", generate_selected_projects),
    ]

    for base_name, generator in static_generators:
        for theme in (DARK, LIGHT):
            path = assets_dir / f"{base_name}_{theme.name}.svg"
            path.write_text(generator(theme), encoding="utf-8")

    for theme in (DARK, LIGHT):
        path = assets_dir / f"portfolio_insights_{theme.name}.svg"
        path.write_text(generate_portfolio_insights(data, theme), encoding="utf-8")

    for legacy in LEGACY_ASSETS:
        legacy_path = assets_dir / legacy
        if legacy_path.exists():
            legacy_path.unlink()

    # Validate XML for each generated file
    for theme in ("dark", "light"):
        for base in ("profile_hero", "focus_areas", "selected_projects", "portfolio_insights"):
            ET.parse(assets_dir / f"{base}_{theme}.svg")
