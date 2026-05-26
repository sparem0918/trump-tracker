# -*- coding: utf-8 -*-
"""
RSS 뉴스 수집 모듈
- config.RSS_FEEDS 의 피드를 병렬 수집
- 로컬 캐시 30분
- 최근 N시간 윈도우 필터
"""
import os
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from html import unescape
import re

import feedparser
from dateutil import parser as dp

import config

CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "news.json")


def _kst_now():
    return datetime.now(timezone(timedelta(hours=9)))


def _strip_html(s):
    """간단 HTML 태그 제거"""
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _parse_entry_dt(entry):
    """엔트리에서 발행 시간 파싱"""
    for key in ("published", "updated", "created"):
        val = entry.get(key)
        if val:
            try:
                dt = dp.parse(val)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone(timedelta(hours=9)))
                return dt
            except Exception:
                continue
    # struct_time 폴백
    for key in ("published_parsed", "updated_parsed"):
        val = entry.get(key)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc).astimezone(
                    timezone(timedelta(hours=9))
                )
            except Exception:
                continue
    return None


def _entry_to_item(entry, feed_info):
    """feedparser entry → 표준 dict"""
    title = _strip_html(entry.get("title", ""))
    summary = _strip_html(entry.get("summary", ""))
    link = entry.get("link", "")
    dt = _parse_entry_dt(entry)

    # id 생성: link 우선, 없으면 title hash
    item_id = entry.get("id") or link or hashlib.md5(title.encode("utf-8")).hexdigest()

    return {
        "id": item_id,
        "title": title,
        "summary": summary,
        "link": link,
        "source": feed_info["name"],
        "source_category": feed_info.get("category", "종합"),
        "published": dt.isoformat() if dt else "",
        "published_dt": dt.isoformat() if dt else "",
    }


def _fetch_feed(feed_info):
    """단일 피드 수집"""
    items = []
    try:
        parsed = feedparser.parse(feed_info["url"])
        for entry in parsed.entries:
            try:
                items.append(_entry_to_item(entry, feed_info))
            except Exception as e:
                print(f"  [경고] {feed_info['name']} 엔트리 처리 실패: {e}")
    except Exception as e:
        print(f"  [오류] {feed_info['name']} 수집 실패: {e}")
    return items


def _within_window(item, hours):
    """시간 윈도우 필터"""
    pub = item.get("published_dt") or item.get("published")
    if not pub:
        return True  # 시간 정보 없으면 일단 포함
    try:
        dt = dp.parse(pub)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone(timedelta(hours=9)))
        cutoff = _kst_now() - timedelta(hours=hours)
        return dt >= cutoff
    except Exception:
        return True


def _load_cache():
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        ts = dp.parse(data.get("generated_at", ""))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone(timedelta(hours=9)))
        age = (_kst_now() - ts).total_seconds() / 60
        if age <= config.CACHE_TTL_MINUTES:
            return data
    except Exception:
        return None
    return None


def _save_cache(data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, default=str)


def _dedupe(items):
    """동일 link 또는 동일 제목 제거"""
    seen_link = set()
    seen_title = set()
    out = []
    for it in items:
        link = it.get("link", "").strip()
        title = it.get("title", "").strip()
        if link and link in seen_link:
            continue
        if title and title in seen_title:
            continue
        if link:
            seen_link.add(link)
        if title:
            seen_title.add(title)
        out.append(it)
    return out


def collect_news(force_refresh=False):
    """RSS 피드를 병렬 수집해서 표준화된 리스트 반환

    반환: {
        "generated_at": ISO string,
        "total_count": int,
        "items": [...]
    }
    """
    if not force_refresh:
        cached = _load_cache()
        if cached:
            print(f"[캐시 사용] {cached.get('total_count', 0)}건")
            return cached

    print(f"[수집 시작] 피드 {len(config.RSS_FEEDS)}개 병렬 수집")

    all_items = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for items in ex.map(_fetch_feed, config.RSS_FEEDS):
            all_items.extend(items)

    # 시간 윈도우 필터
    all_items = [it for it in all_items if _within_window(it, config.NEWS_HOURS_WINDOW)]

    # 중복 제거
    all_items = _dedupe(all_items)

    # 최신순 정렬
    def _sort_key(it):
        dt = it.get("published_dt") or it.get("published") or ""
        try:
            return dp.parse(dt)
        except Exception:
            return _kst_now() - timedelta(days=365)

    all_items.sort(key=_sort_key, reverse=True)

    data = {
        "generated_at": _kst_now().isoformat(),
        "total_count": len(all_items),
        "items": all_items,
    }

    print(f"[수집 완료] 총 {len(all_items)}건")
    _save_cache(data)
    return data
