# -*- coding: utf-8 -*-
"""
버핏 원칙 로더
- data/buffett_investment_method_korean.md 파일에서 원칙 추출
- 매일 다른 원칙 1개를 결정론적 시드로 선택
"""
import os
import re
import hashlib
from datetime import datetime, timezone, timedelta

BUFFETT_MD = os.path.join("data", "buffett_investment_method_korean.md")


def _kst_now():
    return datetime.now(timezone(timedelta(hours=9)))


def _today_seed():
    """오늘 날짜 기반 결정론적 시드 (같은 날엔 같은 원칙)"""
    today = _kst_now().strftime("%Y%m%d")
    return int(hashlib.md5(today.encode()).hexdigest()[:8], 16)


def _extract_principles():
    """MD에서 표 형태로 정리된 원칙 추출"""
    if not os.path.exists(BUFFETT_MD):
        return []

    with open(BUFFETT_MD, "r", encoding="utf-8") as f:
        text = f.read()

    principles = []

    # 2번 섹션의 표에서 추출
    # | 원칙 | 핵심 내용 | 실제 적용 |
    sec2_match = re.search(
        r"## 2\..*?(?=##\s)",
        text, re.DOTALL,
    )
    if sec2_match:
        for line in sec2_match.group(0).split("\n"):
            if line.startswith("|") and "---" not in line and "원칙" not in line.split("|")[1].strip():
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 3:
                    principles.append({
                        "type": "principle",
                        "title": parts[0],
                        "content": parts[1],
                        "application": parts[2],
                    })

    return principles


def _extract_questions():
    """17번 섹션의 매수 전 점검 질문 추출"""
    if not os.path.exists(BUFFETT_MD):
        return []

    with open(BUFFETT_MD, "r", encoding="utf-8") as f:
        text = f.read()

    sec17_match = re.search(
        r"## 17\..*?(?=##\s|\Z)",
        text, re.DOTALL,
    )
    if not sec17_match:
        return []

    questions = []
    for line in sec17_match.group(0).split("\n"):
        m = re.match(r"^\d+\.\s+(.+)", line.strip())
        if m:
            questions.append(m.group(1).strip())
    return questions


def get_buffett_context():
    """템플릿에서 사용할 버핏 데이터 패키지"""
    principles = _extract_principles()
    questions = _extract_questions()

    if not principles and not questions:
        return {"available": False}

    # 매일 다른 원칙 1개 선택 (결정론적)
    daily = None
    if principles:
        idx = _today_seed() % len(principles)
        daily = principles[idx]

    return {
        "available": True,
        "daily_checkpoint": daily,
        "questions": questions[:10],  # 최대 10개
        "one_liner": (
            "차트에서는 비싸게 사지 않는지를 보고, "
            "재무제표에서는 오래 보유할 만큼 좋은 기업인지를 봅니다."
        ),
    }


if __name__ == "__main__":
    ctx = get_buffett_context()
    print(f"available: {ctx['available']}")
    if ctx.get("daily_checkpoint"):
        d = ctx["daily_checkpoint"]
        print(f"오늘의 원칙: {d['title']}")
        print(f"  내용: {d['content']}")
        print(f"  적용: {d['application']}")
    print(f"질문 수: {len(ctx.get('questions', []))}")
