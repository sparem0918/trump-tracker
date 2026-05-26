# -*- coding: utf-8 -*-
"""
Gemini API 종합 요약기
- 트럼프 관련 뉴스를 받아 정책 동향 + 한국 영향 종합 요약 생성
- GEMINI_API_KEY 환경변수 사용 (없으면 None 반환)
- 1시간 캐시 (동일 뉴스 셋에 대해서는 재호출 안 함)
"""
import os
import json
import hashlib
from datetime import datetime, timezone, timedelta

import requests
from dateutil import parser as dp


CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "gemini_brief.json")
CACHE_TTL_MINUTES = 60

# 환경변수
API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()
API_BASE = "https://generativelanguage.googleapis.com/v1beta"

# 요청 한도
MAX_ITEMS = 50
REQUEST_TIMEOUT_SEC = 30


def _kst_now():
    return datetime.now(timezone(timedelta(hours=9)))


def _items_hash(items):
    """뉴스 셋 식별용 해시 (캐시 키)"""
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
    """Gemini 프롬프트 생성"""
    bullets = []
    for it in items[:MAX_ITEMS]:
        title = (it.get("title") or "").strip()
        summary = (it.get("summary") or "").strip()
        source = (it.get("source") or "").strip()
        if not title:
            continue
        bullet = f"- [{source}] {title}"
        if summary:
            bullet += f"\n  {summary[:200]}"
        bullets.append(bullet)

    news_text = "\n".join(bullets)

    prompt = f"""당신은 트럼프 행정부 정책이 한국 경제·산업·증시에 미치는 영향을 분석하는 시니어 애널리스트입니다.

아래는 최근 1주일간 한국·해외 매체에서 보도된 트럼프 행정부 관련 뉴스 {len(items)}건입니다:

{news_text}

위 내용을 바탕으로 다음 JSON 형식으로만 응답하세요. 다른 텍스트나 마크다운은 포함하지 마세요.

규칙:
1. summary: 트럼프 정책 동향이 한국 산업·증시에 미치는 영향을 5-7문장으로 종합. 단순 사실 나열이 아닌 정책 흐름과 한국 영향의 인과관계를 분석적으로 설명. 분석가 톤. 특정 종목 매수·매도 추천 금지.
2. points: 가장 중요한 정책·영향 포인트 4-5개. 각각 한 줄(40-80자). 정책 변화나 한국 산업 영향에 초점.

응답 JSON:
{{
  "summary": "...",
  "points": ["...", "...", "...", "...", "..."]
}}"""
    return prompt


def _call_gemini(prompt, model):
    """Gemini REST API 호출, 파싱된 dict 반환"""
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
            "maxOutputTokens": 2048,
        },
    }
    resp = requests.post(
        url, headers=headers, json=body, timeout=REQUEST_TIMEOUT_SEC
    )
    resp.raise_for_status()
    data = resp.json()

    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini 응답에 candidates 없음")
    text = candidates[0]["content"]["parts"][0]["text"]
    # JSON mime 강제했지만 안전망
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def generate_brief(items, force_refresh=False):
    """트럼프 관련 뉴스 종합 요약 생성

    Args:
        items: 트럼프 관련 뉴스 항목 리스트 (이미 필터링된 상태)
        force_refresh: True면 캐시 무시

    Returns:
        dict 또는 None
        {
            "summary": str,
            "points": [str, ...],
            "news_count": int,
            "model": str,
            "items_hash": str,
            "generated_at": ISO datetime
        }
    """
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

        brief = {
            "summary": result.get("summary", ""),
            "points": result.get("points", []),
            "news_count": len(items),
            "model": DEFAULT_MODEL,
            "items_hash": items_hash,
            "generated_at": _kst_now().isoformat(),
        }
        _save_cache(brief)
        print(f"[Gemini] 요약 완료: {brief['summary'][:60]}...")
        return brief

    except requests.HTTPError as e:
        print(f"[Gemini] HTTP 오류: {e.response.status_code} - {e.response.text[:200]}")
        return None
    except Exception as e:
        print(f"[Gemini] 요약 생성 실패: {type(e).__name__}: {e}")
        return None


if __name__ == "__main__":
    # 단독 실행 테스트
    test_items = [
        {
            "id": "1",
            "title": "트럼프 행정부, 양자컴퓨팅 9곳에 20억달러 지원",
            "summary": "인텔식 지분 확보 모델 재현. 한국 양자 관련주 주목.",
            "source": "한국경제",
        },
        {
            "id": "2",
            "title": "트럼프 반도체 100% 관세 발언, 삼성·SK 타격 우려",
            "summary": "대미 반도체 수출 14.8조원 직격탄 가능성.",
            "source": "매일경제",
        },
    ]
    result = generate_brief(test_items, force_refresh=True)
    if result:
        print("\n=== 요약 ===")
        print(result["summary"])
        print("\n=== 포인트 ===")
        for p in result["points"]:
            print(f" • {p}")
    else:
        print("요약 생성 실패 또는 API 키 없음")
