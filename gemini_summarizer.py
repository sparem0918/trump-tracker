# -*- coding: utf-8 -*-
"""
Gemini API 종합 요약기 - 미국 경제 데일리용
- 미국 경제 뉴스를 받아 거시 동향 + 한국 영향 종합 요약 생성
- GEMINI_API_KEY 환경변수 사용 (없으면 None 반환)
- 1시간 캐시
- thinking 모드 비활성화 (thinkingBudget: 0), maxOutputTokens 8192
"""
import os
import re
import json
import hashlib
from datetime import datetime, timezone, timedelta

import requests
from dateutil import parser as dp


CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "gemini_brief.json")
CACHE_TTL_MINUTES = 60

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()
API_BASE = "https://generativelanguage.googleapis.com/v1beta"

MAX_ITEMS = 50
REQUEST_TIMEOUT_SEC = 60


def _kst_now():
    return datetime.now(timezone(timedelta(hours=9)))


def _items_hash(items):
    ids = sorted([
        str(it.get("id") or it.get("link") or it.get("title", ""))
        for it in items
    ])
    return hashlib.md5("|".join(ids).encode("utf-8")).hexdigest()


def _load_cache(items_hash):
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("items_hash") != items_hash:
            return None
        ts = dp.parse(data["generated_at"])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone(timedelta(hours=9)))
        age = (_kst_now() - ts).total_seconds() / 60
        if age <= CACHE_TTL_MINUTES:
            return data
    except Exception:
        return None
    return None


def _save_cache(data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, default=str)


def _build_prompt(items):
    bullets = []
    for it in items[:MAX_ITEMS]:
        title = (it.get("title") or "").strip()
        summary = (it.get("summary") or "").strip()
        source = (it.get("source") or "").strip()
        if not title:
            continue
        bullet = f"- [{source}] {title}"
        if summary:
            bullet += f"\n  {summary[:180]}"
        bullets.append(bullet)

    news_text = "\n".join(bullets)

    prompt = f"""당신은 미국 경제가 한국 경제·산업·증시에 미치는 영향을 분석하는 시니어 매크로 애널리스트입니다.

아래는 최근 1주일간 보도된 미국 경제 관련 뉴스 {len(items)}건입니다:

{news_text}

위 내용을 바탕으로 다음 JSON 형식으로만 응답하세요. 다른 텍스트나 마크다운은 포함하지 마세요.

규칙:
1. summary: 미국 거시경제(연준·물가·고용·유가·달러)와 주요 산업 동향이 한국 증시·환율·수출에 미치는 영향을 5문장으로 종합. 단순 사실 나열이 아닌 인과관계 중심의 분석적 서술. 매크로 애널리스트 톤. 특정 종목 매수·매도 추천 금지. 300자 이내.
2. points: 가장 중요한 거시·산업 포인트 4개. 각각 한 줄 50자 이내.

JSON 형식만 반환하세요. 큰따옴표 안의 큰따옴표는 작은따옴표로 대체하세요:
{{
  "summary": "...",
  "points": ["...", "...", "...", "..."]
}}"""
    return prompt


def _try_repair_json(text):
    """잘린 JSON 복구 시도"""
    text = text.strip()
    last_brace = text.rfind("}")
    if last_brace > 0:
        candidate = text[:last_brace + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass
    try:
        summary_match = re.search(r'"summary"\s*:\s*"([^"]*?)"', text, re.DOTALL)
        summary = summary_match.group(1) if summary_match else ""
        points = []
        points_section = re.search(r'"points"\s*:\s*\[(.*?)\]', text, re.DOTALL)
        if points_section:
            points = re.findall(r'"([^"]+)"', points_section.group(1))
        if summary or points:
            return {"summary": summary, "points": points[:5]}
    except Exception:
        pass
    return None


def _call_gemini(prompt, model):
    url = f"{API_BASE}/models/{model}:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": API_KEY,
    }
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json",
            "maxOutputTokens": 8192,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    resp = requests.post(url, headers=headers, json=body, timeout=REQUEST_TIMEOUT_SEC)
    resp.raise_for_status()
    data = resp.json()

    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError(f"Gemini 응답에 candidates 없음. raw={str(data)[:300]}")

    finish_reason = candidates[0].get("finishReason", "")
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise ValueError(f"응답 parts 비어 있음. finishReason={finish_reason}")

    text = parts[0].get("text", "").strip()
    if not text:
        raise ValueError(f"응답 text 비어 있음. finishReason={finish_reason}")

    print(f"[Gemini] 응답 수신 (finishReason={finish_reason}, {len(text)}자)")

    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[Gemini] 1차 파싱 실패: {e}. 복구 시도...")
        repaired = _try_repair_json(text)
        if repaired:
            print(f"[Gemini] 복구 성공")
            return repaired
        print(f"[Gemini] 응답 마지막 200자: ...{text[-200:]}")
        raise


def generate_brief(items, force_refresh=False):
    if not API_KEY:
        print("[Gemini] GEMINI_API_KEY 환경변수가 없습니다. 요약 건너뜀.")
        return None

    if not items:
        print("[Gemini] 처리할 뉴스가 없습니다.")
        return None

    items_hash = _items_hash(items)

    if not force_refresh:
        cached = _load_cache(items_hash)
        if cached:
            print(f"[Gemini] 캐시 사용 (hash={items_hash[:8]}, {len(items)}건)")
            return cached

    try:
        print(f"[Gemini] 종합 요약 생성 중... ({len(items)}건, model={DEFAULT_MODEL})")
        prompt = _build_prompt(items)
        result = _call_gemini(prompt, DEFAULT_MODEL)

        summary = (result.get("summary") or "").strip()
        points = result.get("points") or []
        if not summary and not points:
            print("[Gemini] 결과가 비어 있음")
            return None

        brief = {
            "summary": summary,
            "points": [p.strip() for p in points if p and p.strip()][:5],
            "news_count": len(items),
            "model": DEFAULT_MODEL,
            "items_hash": items_hash,
            "generated_at": _kst_now().isoformat(),
        }
        _save_cache(brief)
        print(f"[Gemini] 요약 완료: {brief['summary'][:60]}...")
        return brief

    except requests.HTTPError as e:
        body = ""
        try:
            body = e.response.text[:300]
        except Exception:
            pass
        print(f"[Gemini] HTTP 오류: {e.response.status_code} - {body}")
        return None
    except Exception as e:
        print(f"[Gemini] 요약 생성 실패: {type(e).__name__}: {e}")
        return None
