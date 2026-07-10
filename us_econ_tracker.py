# -*- coding: utf-8 -*-
"""
미국 경제 트래커 (us_econ_tracker.py)

기존 trump_tracker 로직을 재사용하되, 토픽을 macro/sector 두 그룹으로
분리하여 반환. macro는 kr_comment, sector는 stocks를 포함.
"""
from datetime import datetime, timezone, timedelta
from collections import OrderedDict
import re

import us_econ_config as cfg


def _now_kst():
    return datetime.now(timezone(timedelta(hours=9)))


def _parse_dt(value):
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def _text_of(item):
    parts = [item.get("title", ""), item.get("summary", "")]
    kp = item.get("key_points", [])
    if isinstance(kp, list):
        parts.extend(kp)
    return " ".join(p for p in parts if p)


def _contains_any(text, keywords):
    if not text:
        return False
    low = text.lower()
    return any(kw.lower() in low for kw in keywords)


def is_us_econ_related(item):
    return _contains_any(_text_of(item), cfg.US_ECON_KEYWORDS)


def detect_topics(item):
    text = _text_of(item)
    matched = []
    for name, conf in cfg.US_ECON_TOPICS.items():
        if _contains_any(text, conf["keywords"]):
            matched.append(name)
    return matched


_IMPACT_KW = [
    "급등", "급락", "최고", "최저", "돌파", "폭등", "폭락", "동결",
    "인상", "인하", "관세", "발표", "전망", "협상", "타결",
]
_NUM_RE = re.compile(r"\d[\d,\.]*")


def _score_item(item):
    text = _text_of(item)
    score = min(len(_NUM_RE.findall(text)), 5)
    for kw in _IMPACT_KW:
        if kw in text:
            score += 2
    score += min(len(text) // 60, 5)
    return score


def _within_window(item, hours):
    dt = _parse_dt(item.get("published_dt") or item.get("published"))
    if not dt:
        return True
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone(timedelta(hours=9)))
    return dt >= _now_kst() - timedelta(hours=hours)


def build_us_econ_section(all_items):
    """
    Returns:
        {
            "total_count": int,
            "macro_topics": [ {name, icon, description, kr_comment, items, count}, ... ],
            "sector_topics": [ {name, icon, description, stocks, items, count}, ... ],
            "uncategorized": [...],
            "generated_at": iso,
        }
    """
    if not all_items:
        return {
            "total_count": 0, "macro_topics": [], "sector_topics": [],
            "uncategorized": [], "generated_at": _now_kst().isoformat(),
        }

    econ_items = [
        it for it in all_items
        if _within_window(it, cfg.US_ECON_NEWS_HOURS_WINDOW)
        and is_us_econ_related(it)
    ]

    grouped = OrderedDict((name, []) for name in cfg.US_ECON_TOPICS.keys())
    uncategorized = []
    seen = {name: set() for name in grouped}

    for it in econ_items:
        topics = detect_topics(it)
        if not topics:
            uncategorized.append(it)
            continue
        # 정의 순서 우선순위로 첫 매칭 토픽에 배치
        for name in cfg.US_ECON_TOPICS.keys():
            if name in topics:
                item_id = it.get("id") or it.get("link") or it.get("title", "")
                if item_id in seen[name]:
                    break
                grouped[name].append(it)
                seen[name].add(item_id)
                break

    macro_out, sector_out = [], []
    for name, items in grouped.items():
        if not items:
            continue
        conf = cfg.US_ECON_TOPICS[name]
        items_sorted = sorted(items, key=_score_item, reverse=True)
        items_sorted = items_sorted[: cfg.MAX_NEWS_PER_TOPIC]

        base = {
            "name": name,
            "icon": conf.get("icon", "•"),
            "description": conf.get("description", ""),
            "items": items_sorted,
            "count": len(items),
        }

        if conf.get("kind") == "macro":
            base["kr_comment"] = conf.get("kr_comment", "")
            macro_out.append(base)
        else:
            stocks = cfg.TOPIC_STOCKS.get(name, [])
            base["stocks"] = stocks[: cfg.MAX_STOCKS_PER_TOPIC]
            sector_out.append(base)

    macro_out.sort(key=lambda x: x["count"], reverse=True)
    sector_out.sort(key=lambda x: x["count"], reverse=True)
    macro_out = macro_out[: cfg.MAX_MACRO_DISPLAYED]
    sector_out = sector_out[: cfg.MAX_SECTOR_DISPLAYED]

    return {
        "total_count": len(econ_items),
        "macro_topics": macro_out,
        "sector_topics": sector_out,
        "uncategorized": uncategorized[:5],
        "generated_at": _now_kst().isoformat(),
    }
