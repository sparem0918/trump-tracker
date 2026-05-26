# -*- coding: utf-8 -*-
"""
Gemini API 종합 요약기 v2
- 트럼프 관련 뉴스를 받아 정책 동향 + 한국 영향 종합 요약 생성
- GEMINI_API_KEY 환경변수 사용 (없으면 None 반환)
- 1시간 캐시 (동일 뉴스 셋에 대해서는 재호출 안 함)

v2 변경 사항:
- gemini-2.5-flash thinking 모드 비활성화 (응답 잘림 방지)
- maxOutputTokens 8192로 상향
- 잘린 JSON 응답에 대한 견고한 복구 로직 추가
- 디버깅용 응답 미리보기 로그
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
REQUEST_TIMEOUT_SEC = 60   # thinking 모드 비활성화 후에도 안전 마진


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

    prompt = f"""당신은 트럼프 행정부 정책이 한국 경제·산업·증시에 미치는 영향을 분석하는 시니어 애널리스트입니다.

아래는 최근 1주일간 한국·해외 매체에서 보도된 트럼프 행정부 관련 뉴스 {len(items)}건입니다:

{news_text}

위 내용을 바탕으로 다음 JSON 형식으로만 응답하세요. 다른 텍스트나 마크다운은 포함하지 마세요.

규칙:
1. summary: 트럼프 정책 동향이 한국 산업·증시에 미치는 영향을 5문장으로 종합. 단순 사실 나열이 아닌 정책 흐름과 한국 영향의 인과관계를 분석적으로 설명. 분석가 톤. 특정 종목 매수·매도 추천 금지. 300자 이내.
2. points: 가장 중요한 정책·영향 포인트 4개. 각각 한 줄 50자 이내. 정책 변화나 한국 산업 영향에 초점.

JSON 형식만 반환하세요. 큰따옴표 안의 큰따옴표는 작은따옴표로 대체하세요:
{{
  "summary": "...",
  "points": ["...", "...", "...", "..."]
}}"""
    return prompt


def _try_repair_json(text):
    """잘린 JSON 복구 시도 - 마지막 닫힌 괄호 위치 찾아 잘라내기"""
    text = text.strip()
    # 1) 흔한 케이스: 마지막 } 까지 자르기
    last_brace = text.rfind("}")
    if last_brace > 0:
        candidate = text[:last_brace + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass
    # 2) summary와 points를 정규식으로 직접 추출
    try:
        summary_match = re.search(
            r'"summary"\s*:\s*"([^"]*?)"', text, re.DOTALL,
        )
        summary = summary_match.group(1) if summary_match else ""
        points = re.findall(r'"([^"]{8,100})"', text)
        # points 배열 안 항목만 추출 시도
        points_section = re.search(
            r'"points"\s*:\s*\[(.*?)\]', text, re.DOTALL,
        )
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
            # 핵심: gemini-2.5-* 의 thinking 모드 비활성화
            # thinking이 토큰을 잡아먹어 본문이 잘리는 현상 방지
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    resp = requests.post(
        url, headers=headers, json=body, timeout=REQUEST_TIMEOUT_SEC
    )
    resp.raise_for_status()
    data = resp.json()

    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError(f"Gemini 응답에 candidates 없음. raw={str(data)[:300]}")

    finish_reason = candidates[0].get("finishReason", "")
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise ValueError(
            f"응답 parts 비어 있음. finishReason={finish_reason}. "
            f"raw={str(data)[:300]}"
        )

    text = parts[0].get("text", "").strip()
    if not text:
        raise ValueError(f"응답 text 비어 있음. finishReason={finish_reason}")

    # 디버깅용 미리보기
    print(f"[Gemini] 응답 수신 (finishReason={finish_reason}, {len(text)}자)")

    # 마크다운 펜스 제거
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    # 1차 시도: 그대로 파싱
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[Gemini] 1차 파싱 실패: {e}. 복구 시도...")
        # 2차 시도: 잘린 응답 복구
        repaired = _try_repair_json(text)
        if repaired:
            print(f"[Gemini] 복구 성공: summary {len(repaired.get('summary',''))}자, points {len(repaired.get('points',[]))}개")
            return repaired
        # 마지막 디버깅: 응답 끝부분 보여주기
        print(f"[Gemini] 응답 마지막 200자: ...{text[-200:]}")
        raise


def generate_brief(items, force_refresh=False):
    """트럼프 관련 뉴스 종합 요약 생성"""
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
        # 빈 결과 가드
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


if __name__ == "__main__":
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
