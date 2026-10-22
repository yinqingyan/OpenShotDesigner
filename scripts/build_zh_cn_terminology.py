#!/usr/bin/env python3
"""Build the shared Chinese terminology review data."""

from __future__ import annotations

import json
from pathlib import Path

from build_zh_cn_drafts import GLOSSARY, PHRASE_TRANSLATIONS


ROOT = Path(__file__).resolve().parent.parent
LOCALIZATION = ROOT / "localization" / "zh-CN"
CATALOG = LOCALIZATION / "english-source-catalog.json"
OUTPUT = LOCALIZATION / "zh-cn-terminology.json"


def term_area(source: str) -> str:
    value = source.casefold()
    groups = [
        (("camera", "shot", "focal", "aperture", "sensor", "exposure", "lens"), "摄影"),
        (("light", "fixture", "power", "circuit", "truss", "rig", "dmx", "electric"), "灯光/电力"),
        (("cast", "crew", "production", "call", "wrap", "budget", "rate", "meal"), "制片"),
        (("scene", "script", "screenplay", "slugline", "shot list", "storyboard"), "编剧/导演"),
        (("continuity", "take", "wardrobe", "make-up", "sound"), "场记/声音"),
        (("pdf", "print", "report", "export"), "报表/导出"),
    ]
    for needles, area in groups:
        if any(needle in value for needle in needles):
            return area
    return "程序界面"


def build() -> Path:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    rows: list[dict] = []
    known: set[str] = set()

    def add(source: str, translation: str, confidence: str, note: str, method: str) -> None:
        key = source.casefold()
        if key in known or not translation or source == translation:
            return
        area = term_area(source)
        rows.append(
            {
                "id": f"TERM-{len(rows) + 1:04d}",
                "entry_type": "术语",
                "source": source,
                "module": f"术语/{area}",
                "pdf": False,
                "translation": translation,
                "status": "待确认",
                "disposition": "术语初译",
                "confidence": confidence,
                "context_note": f"{area}领域术语。{note} 此术语确认后会作为界面合成时的首选译名。",
                "reason": "",
                "method": method,
            }
        )
        known.add(key)

    for term in catalog["terminology"]:
        add(
            term["source"],
            term["suggestion"],
            term["confidence"],
            term["note"],
            "curated",
        )
    for source, translation in PHRASE_TRANSLATIONS.items():
        add(
            source,
            translation,
            "中",
            "由专业短语表扩充；请结合画面、表头和字段语境确认。",
            "phrase",
        )
    for source, translation in GLOSSARY.items():
        add(
            source,
            translation,
            "中",
            "术语库基础译名；同一英文词在不同面板可能采用不同表述。",
            "glossary",
        )

    output = {
        "metadata": {
            "project": catalog["metadata"]["project"],
            "sourceCommit": catalog["metadata"]["commit"],
            "method": "电影制作、摄影、灯光、电力、制片、场记与程序界面术语初译",
            "counts": {"entries": len(rows), "status:待确认": len(rows)},
        },
        "entries": rows,
    }
    OUTPUT.write_text(f"{json.dumps(output, ensure_ascii=False, indent=2)}\n", encoding="utf-8")
    return OUTPUT


if __name__ == "__main__":
    print(build())
