#!/usr/bin/env python3
"""Improve long-form localization drafts with a machine translation pass.

Exact interface labels and established industry phrases stay under local
control. Longer messages are translated in bounded batches, then corrected by
the project's film-production terminology. The script writes an explicit
provider/method record so no row looks like a completed human review.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

from build_zh_cn_drafts import (
    EXACT_OVERRIDES,
    GLOSSARY,
    OUTPUT,
    PHRASE_TRANSLATIONS,
    module_context,
    normalise,
    parse_dictionary,
    should_preserve,
    translate_text,
)


ENDPOINT = "https://translate.googleapis.com/translate_a/single"
BATCH_SIZE = 40
MAX_RETRIES = 5
KEEP_LOCAL_METHODS = {"exact", "dictionary", "pattern"}


TERM_GUARDS = {
    "Shot size": "景别",
    "Good take": "可用条次",
    "Planned wrap": "计划收工",
    "Crew call": "剧组集合时间",
    "Cast call": "演员集合时间",
    "Unit base": "剧组停车点",
    "Call sheet": "通告单",
    "Run of Show": "节目流程单",
    "Above the line": "线上成本",
    "Below the line": "线下成本",
    "Focal Point": "焦点",
    "White Point": "白点",
    "Camera Aperture": "摄影机光圈",
    "Shutter Speed": "快门速度",
    "Shutter Angle": "快门角度",
    "Continuity": "场记",
    "Coverage": "镜头覆盖",
    "Floor plan": "拍摄平面图",
    "Shot list": "镜头表",
    "Storyboard": "故事板",
    "Viewfinder": "取景器",
    "Scene setup": "场次机位设置",
    "Setup": "机位设置",
    "Take": "条次",
    "Wild track": "独立音轨",
    "MOS": "MOS",
    "DMX": "DMX",
    "ISO": "ISO",
    "FPS": "FPS",
    "T-stop": "T 档",
    "ND filter": "ND 滤镜",
    "headroom": "余量",
    "truss": "桁架",
    "rigging": "灯光吊挂",
    "fixture": "灯具",
    "circuit": "回路",
    "generator": "发电机",
    "house supply": "现场建筑供电",
    "shooting day": "拍摄日",
    "good take": "可用条次",
    "wild track": "独立音轨",
    "call sheet": "通告单",
    "run of show": "节目流程单",
    "above the line": "线上成本",
    "below the line": "线下成本",
}


PROPER_NOUN_GUARDS = [
    "Open Shot Designer",
    "OpenShotDesigner",
    "DaVinci Resolve",
    "Final Draft",
    "OpenStreetMap",
    "Google Drive",
    "Nextcloud",
    "WebDAV",
    "Grass Valley",
    "Avid Media Composer",
    "Avid ALE",
    "Anton Bauer",
    "Dana Dolly",
    "Hotel Astoria",
    "V-Mount",
    "SAG-AFTRA",
    "Layout",
]


BAD_TARGET_TERMS = {
    "相机": "摄影机",
    "摄影机相机": "摄影机",
    "摄像机": "摄影机",
    "摄影机位": "机位",
    "射击列表": "镜头表",
    "拍摄清单": "镜头表",
    "拍摄列表": "镜头表",
    "连续性冲突": "场记连续性冲突",
    "连续性日志": "场记记录",
    "连续性原木": "场记记录",
    "船员呼叫": "剧组集合时间",
    "全体工作人员通话": "剧组集合时间",
    "单位基地": "剧组停车点",
    "电话表": "通告单",
    "通话表": "通告单",
    "运行节目": "节目流程单",
    "运行秀": "节目流程单",
    "白点（开尔文）": "白点（Kelvin）",
    "上方线": "线上成本",
    "下方线": "线下成本",
    "线下（总）": "线下成本（总额）",
    "线上（总）": "线上成本（总额）",
    "拍摄尺寸": "景别",
    "镜头尺寸": "景别",
    "镜头大小": "景别",
    "好主意": "可用条次",
    "良好的拍摄": "可用条次",
    "拍摄效果好": "可用条次",
    "拍得好": "可用条次",
    "计划包裹": "计划收工",
    "计划结束": "计划收工",
    "所有项目（仪表板）": "所有项目（项目总览）",
    "谷仓门": "四叶挡板",
    "固定装置": "灯具",
    "夹具": "灯具",
    "摄像头": "摄影机",
    "注射尺寸": "景别",
    "注射量": "景别",
    "家庭电源": "现场建筑供电",
    "船员": "剧组",
    "套件配件清单": "摄影机套装配件清单",
    "未定稿": "未拍摄",
}


SOURCE_TO_TARGET_REWRITES: list[tuple[str, str]] = [
    (r"\bshot size\b", "景别"),
    (r"\bgood take\b", "可用条次"),
    (r"\bplanned wrap\b", "计划收工"),
    (r"\bcrew call\b", "剧组集合时间"),
    (r"\bcast call\b", "演员集合时间"),
    (r"\bunit base\b", "剧组停车点"),
    (r"\bcall sheets?\b", "通告单"),
    (r"\brun of show\b", "节目流程单"),
    (r"\babove the line\b", "线上成本"),
    (r"\bbelow the line\b", "线下成本"),
    (r"\bcontinuity\b", "场记"),
    (r"\bcamera\b", "摄影机"),
    (r"\bscene setup\b", "场次机位设置"),
    (r"\bshot list\b", "镜头表"),
    (r"\bfloor plan\b", "拍摄平面图"),
    (r"\bwhite point\b", "白点"),
    (r"\bgross\b", "总额"),
]


def source_phrase_correction(source: str, translation: str) -> str:
    result = translation
    for trigger, chinese in SOURCE_TO_TARGET_REWRITES:
        if re.search(trigger, source, flags=re.I):
            # Protect the intended term if the provider selected a synonym.
            for bad, good in BAD_TARGET_TERMS.items():
                if good == chinese:
                    result = result.replace(bad, good)
    for bad, good in BAD_TARGET_TERMS.items():
        result = result.replace(bad, good)
    result = re.sub(r"\s+([，。！？；：])", r"\1", result)
    result = re.sub(r"([，。！？；：])(?=[^\s\n])", r"\1", result)
    result = re.sub(r"[ \t]+", " ", result)
    return result.strip()


def recover_private_markers(source: str, translation: str) -> str:
    """Recover placeholders from the first pass's private-use guard tokens.

    The first provider run normalized some private-use marker endings. The
    numeric index survived, and the guard order is deterministic, so rerunning
    locally avoids sending those strings back through the provider.
    """
    guarded_values: list[str] = []
    for value in PROPER_NOUN_GUARDS:
        if re.search(rf"(?<![A-Za-z]){re.escape(value)}(?![A-Za-z])", source, flags=re.I):
            guarded_values.append(value)
    guarded_values.extend(
        match.group(0)
        for match in re.finditer(r"\$\{.*?\}|\{[A-Za-z][\w.[\]-]*\}", source)
    )

    def replace(match: re.Match[str]) -> str:
        index = int(match.group(1))
        return guarded_values[index] if index < len(guarded_values) else match.group(0)

    return re.sub(r"[\ue000-\uf8ff](\d+)(?:[\ue000-\uf8ff])?", replace, translation)


def translate_batch(sources: list[str]) -> list[str]:
    separators = [f"§{i:06d}§" for i in range(len(sources))]
    text = "".join(f"{separators[index]}{source}\n" for index, source in enumerate(sources))
    payload = urllib.parse.urlencode(
        {
            "client": "gtx",
            "sl": "en",
            "tl": "zh-CN",
            "dt": "t",
            "q": text,
        }
    ).encode()
    request = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        data = json.load(response)
    translated = "".join(segment[0] for segment in data[0])
    # Recover using the visible numeric portion, which remains stable under
    # translation. Source variables are left intact; the provider preserves
    # ${...} placeholders reliably.
    positions: list[tuple[int, int]] = []
    for index in range(len(sources)):
        needle = f"{index:06d}"
        position = translated.find(needle)
        if position == -1:
            raise ValueError(f"Translation marker {index} missing")
        positions.append((index, position))

    results: list[str] = []
    for item_index, (index, position) in enumerate(positions):
        start = position + len(f"{index:06d}")
        end = positions[item_index + 1][1] if item_index + 1 < len(positions) else len(translated)
        value = translated[start:end]
        value = re.sub(r"^[^\w\u4e00-\u9fff]+", "", value)
        value = re.sub(r"[^\w\u4e00-\u9fff]+$", "", value)
        results.append(normalise(value))
    return results


def translate_with_retry(sources: list[str]) -> list[str]:
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return translate_batch(sources)
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as error:
            last_error = error
            if attempt == MAX_RETRIES:
                break
            time.sleep(min(2**attempt, 12))
    raise RuntimeError(f"Translation batch failed after {MAX_RETRIES} attempts: {last_error}")


def confidence_for_machine(source: str, translation: str) -> tuple[str, str]:
    if translation == source:
        return "低", "翻译服务未能可靠改写；请人工完成初译。"
    remaining = re.findall(
        r"\b[A-Za-z][A-Za-z'’-]{2,}\b",
        re.sub(r"\$\{.*?\}", " ", translation),
    )
    common_ascii = {
        "AI",
        "ALE",
        "AV",
        "CSV",
        "DMX",
        "DP",
        "FPS",
        "ISO",
        "MOS",
        "MVR",
        "ND",
        "PDF",
        "SAG",
        "OFL",
        "T",
        "VA",
    }
    remaining = [word for word in remaining if word not in common_ascii]
    if len(remaining) <= 2:
        return "中", "完整句已由翻译服务生成；专业术语已按项目术语表校正。"
    return "低", "句子已生成中文初稿，但仍有较多未译词；请重点核对专业含义。"


def main() -> Path:
    data = json.loads(OUTPUT.read_text(encoding="utf-8"))
    repair_only = "--repair-only" in sys.argv
    local_repair = "--local-repair" in sys.argv

    if local_repair:
        for entry in data["entries"]:
            source = str(entry["source"])
            preserve, preserve_reason = should_preserve(source, str(entry.get("module", "")))
            if preserve:
                entry["translation"] = source
                entry["status"] = "待确认"
                entry["disposition"] = "保留英文"
                entry["confidence"] = "不适用"
                entry["method"] = "preserve"
                entry["reason"] = preserve_reason
                entry["context_note"] = (
                    f"{module_context(str(entry.get('module', '')))} {preserve_reason}"
                )
                continue

            translation = recover_private_markers(source, str(entry["translation"]))
            override_method: str | None = None
            if source in EXACT_OVERRIDES:
                translation = EXACT_OVERRIDES[source]
                override_method = "exact"
            elif source in parse_dictionary():
                translation = parse_dictionary()[source]
                override_method = "dictionary"
            elif source in PHRASE_TRANSLATIONS:
                translation = PHRASE_TRANSLATIONS[source]
                override_method = "phrase"
            translation = source_phrase_correction(source, translation)
            if source == translation or re.search(r"[\ue000-\uf8ff]|§\d{6}§", translation):
                fallback, fallback_method = translate_text(source)
                translation = fallback
                entry["method"] = fallback_method
                entry["confidence"] = "低"
                entry["context_note"] = (
                    f"{module_context(str(entry.get('module', '')))} "
                    "批量初译存在未恢复标记，已回退到术语规则原稿；请人工核对或补译。"
                )
            else:
                if override_method in {"exact", "dictionary"}:
                    entry["confidence"] = "高"
                    confidence_note = "已匹配当前中文界面词典或明确的专业标签译名。"
                    entry["method"] = override_method
                elif override_method == "phrase":
                    entry["confidence"] = "中"
                    confidence_note = "核心专业短语已匹配；需结合面板语境确认。"
                    entry["method"] = override_method
                else:
                    entry["confidence"], confidence_note = confidence_for_machine(source, translation)
                    entry["method"] = "machine+glossary"
                entry["context_note"] = (
                    f"{module_context(str(entry.get('module', '')))} "
                    f"{confidence_note} 当前仍待逐条确认。"
                )
            source_slots = Counter(re.findall(r"\$\{.*?\}|\{[A-Za-z][\w.[\]-]*\}", source))
            translated_slots = Counter(re.findall(r"\$\{.*?\}|\{[A-Za-z][\w.[\]-]*\}", translation))
            if source_slots != translated_slots:
                translation = source
                entry["confidence"] = "不适用"
                entry["method"] = "preserve"
                entry["reason"] = "模板变量未能在初译中安全保留，暂按源代码保留。"
                entry["context_note"] = (
                    f"{module_context(str(entry.get('module', '')))} "
                    "检测到变量数量或内容不一致；为避免运行错误，先保留英文并等待人工判断。"
                )
            entry["translation"] = translation
            entry["status"] = "待确认"
            entry["disposition"] = "保留英文" if entry["method"] == "preserve" else "初译"
            if entry["disposition"] == "初译":
                entry["reason"] = ""

        counts = Counter()
        for entry in data["entries"]:
            counts["entries"] += 1
            counts[f"status:{entry['status']}"] += 1
            counts[f"disposition:{entry['disposition']}"] += 1
            counts[f"confidence:{entry['confidence']}"] += 1
            counts[f"method:{entry['method']}"] += 1
        data["metadata"]["counts"] = dict(sorted(counts.items()))
        data["metadata"]["localMarkerRepair"] = True
        OUTPUT.write_text(f"{json.dumps(data, ensure_ascii=False, indent=2)}\n", encoding="utf-8")
        print(OUTPUT)
        return OUTPUT

    pending = [
        entry
        for entry in data["entries"]
        if entry["disposition"] == "初译" and entry.get("method") not in KEEP_LOCAL_METHODS
        and (
            not repair_only
            or entry["source"] == entry["translation"]
            or entry["confidence"] == "低"
            or bool(re.search(r"[\ue000-\uf8ff]|§\d{6}§", str(entry["translation"])))
        )
    ]
    completed = 0

    for batch_start in range(0, len(pending), BATCH_SIZE):
        batch = pending[batch_start : batch_start + BATCH_SIZE]
        translations = translate_with_retry([str(entry["source"]) for entry in batch])
        for entry, translated in zip(batch, translations):
            source = str(entry["source"])
            if source in EXACT_OVERRIDES:
                translated = EXACT_OVERRIDES[source]
            elif source in PHRASE_TRANSLATIONS:
                translated = PHRASE_TRANSLATIONS[source]
            translated = source_phrase_correction(source, translated)
            entry["translation"] = translated
            entry["method"] = "machine+glossary"
            entry["confidence"], confidence_note = confidence_for_machine(entry["source"], translated)
            entry["context_note"] = (
                f"{module_context(str(entry.get('module', '')))} "
                f"{confidence_note} 当前仍待逐条确认。"
            )
        completed += len(batch)
        print(f"translated {completed}/{len(pending)}", flush=True)
        time.sleep(0.15)

    counts = Counter()
    for entry in data["entries"]:
        counts["entries"] += 1
        counts[f"status:{entry['status']}"] += 1
        counts[f"disposition:{entry['disposition']}"] += 1
        counts[f"confidence:{entry['confidence']}"] += 1
        counts[f"method:{entry['method']}"] += 1
    data["metadata"]["translationProvider"] = "Google Translate public gtx endpoint (first pass only)"
    data["metadata"]["machineTranslationBatchSize"] = BATCH_SIZE
    data["metadata"]["counts"] = dict(sorted(counts.items()))
    data["metadata"]["method"] = (
        "专业术语表控制短标签；长句使用翻译服务生成初稿后再按片场语境校正；"
        "所有项目默认等待逐条人工确认"
    )
    OUTPUT.write_text(f"{json.dumps(data, ensure_ascii=False, indent=2)}\n", encoding="utf-8")
    print(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    main()
