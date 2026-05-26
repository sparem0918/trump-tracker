# -*- coding: utf-8 -*-
"""
트럼프 임팩트 트래커 - Flask 메인
- 메인 페이지: 트럼프 영향 토픽별 분류 + 관련주
- Gemini 종합 요약 (GEMINI_API_KEY 환경변수)
- 버핏 원칙: 테마주 매수 전 점검 가이드로 활용
"""
import os
import sys
from datetime import datetime, timezone, timedelta

from flask import Flask, render_template, jsonify, request

import config
import news_collector
import trump_tracker
import trump_config
import buffett_loader
import gemini_summarizer


# Windows 콘솔 한글 출력
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


app = Flask(__name__)


def _kst_now():
    return datetime.now(timezone(timedelta(hours=9)))


def format_korean_date(dt):
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    return f"{dt.year}년 {dt.month}월 {dt.day}일 {weekdays[dt.weekday()]}요일"


def format_relative_time(dt_str):
    if not dt_str:
        return ""
    try:
        from dateutil import parser as dp
        dt = dp.parse(dt_str)
        now = _kst_now()
        diff = now - dt
        s = diff.total_seconds()
        if s < 60:
            return "방금"
        elif s < 3600:
            return f"{int(s / 60)}분 전"
        elif s < 86400:
            return f"{int(s / 3600)}시간 전"
        elif s < 86400 * 2:
            return "어제"
        else:
            return f"{int(s / 86400)}일 전"
    except Exception:
        return ""


app.jinja_env.filters["relative_time"] = format_relative_time


def _collect_trump_items(trump_section):
    """trump_section 안의 모든 트럼프 뉴스를 단일 리스트로 모음 (Gemini 입력용)"""
    out = []
    seen = set()
    for topic in trump_section.get("topics", []):
        for it in topic.get("items", []):
            key = it.get("id") or it.get("link") or it.get("title", "")
            if key in seen:
                continue
            seen.add(key)
            out.append(it)
    for it in trump_section.get("uncategorized", []):
        key = it.get("id") or it.get("link") or it.get("title", "")
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


@app.route("/")
def index():
    """메인: 트럼프 임팩트 트래커"""
    force = request.args.get("refresh") == "1"
    raw = news_collector.collect_news(force_refresh=force)
    items = raw.get("items", [])

    trump_section = trump_tracker.build_trump_section(items)
    buffett = buffett_loader.get_buffett_context()

    # Gemini 종합 요약 (트럼프 관련 뉴스만 입력)
    trump_items_for_brief = _collect_trump_items(trump_section)
    brief = gemini_summarizer.generate_brief(
        trump_items_for_brief,
        force_refresh=force,
    )

    now = _kst_now()

    return render_template(
        "index.html",
        date_str=format_korean_date(now),
        time_str=now.strftime("%H:%M"),
        total_count=raw.get("total_count", 0),
        trump_section=trump_section,
        brief=brief,
        buffett=buffett,
        generated_at=raw.get("generated_at"),
        topics_meta=trump_config.TRUMP_TOPICS,
    )


@app.route("/api/trump")
def api_trump():
    """JSON API: 트럼프 섹션 데이터"""
    force = request.args.get("refresh") == "1"
    raw = news_collector.collect_news(force_refresh=force)
    items = raw.get("items", [])
    section = trump_tracker.build_trump_section(items)
    return jsonify(section)


@app.route("/api/brief")
def api_brief():
    """JSON API: Gemini 요약만"""
    force = request.args.get("refresh") == "1"
    raw = news_collector.collect_news(force_refresh=force)
    items = raw.get("items", [])
    section = trump_tracker.build_trump_section(items)
    trump_items = _collect_trump_items(section)
    brief = gemini_summarizer.generate_brief(trump_items, force_refresh=force)
    return jsonify(brief or {"error": "no_brief"})


@app.route("/api/refresh")
def api_refresh():
    """캐시 강제 갱신"""
    raw = news_collector.collect_news(force_refresh=True)
    return jsonify({
        "status": "ok",
        "count": raw.get("total_count", 0),
        "generated_at": raw.get("generated_at"),
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "time": _kst_now().isoformat(),
        "gemini_enabled": bool(os.environ.get("GEMINI_API_KEY", "").strip()),
    })


if __name__ == "__main__":
    print("=" * 60)
    print("Trump Impact Tracker")
    print("=" * 60)
    print(f"  주소        : http://localhost:{config.PORT}")
    print(f"  로컬망      : http://<PC-IP>:{config.PORT}")
    print(f"  강제갱신    : http://localhost:{config.PORT}/?refresh=1")
    has_key = bool(os.environ.get("GEMINI_API_KEY", "").strip())
    print(f"  Gemini API  : {'활성화' if has_key else '비활성화 (GEMINI_API_KEY 환경변수 없음)'}")
    print("=" * 60)
    print("  종료하려면 Ctrl+C 를 누르세요.")
    print("=" * 60)
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
