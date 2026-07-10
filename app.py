# -*- coding: utf-8 -*-
"""
미국 경제 데일리 - Flask 메인
- 거시(macro): 한국 영향 코멘트 / 산업(sector): 한국 관련주
- Gemini 종합 요약 (GEMINI_API_KEY 환경변수)
- 버핏 원칙: 매수 전 점검 가이드
"""
import os
import sys
from datetime import datetime, timezone, timedelta

from flask import Flask, render_template, jsonify, request

import config
import news_collector
import us_econ_tracker
import buffett_loader
import gemini_summarizer


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
        s = (_kst_now() - dt).total_seconds()
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


def _collect_econ_items(section):
    """섹션 안의 모든 미국 경제 뉴스를 단일 리스트로 (Gemini 입력용)"""
    out, seen = [], set()
    for group in ("macro_topics", "sector_topics"):
        for topic in section.get(group, []):
            for it in topic.get("items", []):
                key = it.get("id") or it.get("link") or it.get("title", "")
                if key in seen:
                    continue
                seen.add(key)
                out.append(it)
    for it in section.get("uncategorized", []):
        key = it.get("id") or it.get("link") or it.get("title", "")
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


@app.route("/")
def index():
    force = request.args.get("refresh") == "1"
    raw = news_collector.collect_news(force_refresh=force)
    items = raw.get("items", [])

    section = us_econ_tracker.build_us_econ_section(items)
    buffett = buffett_loader.get_buffett_context()

    econ_items = _collect_econ_items(section)
    brief = gemini_summarizer.generate_brief(econ_items, force_refresh=force)

    now = _kst_now()

    return render_template(
        "index.html",
        date_str=format_korean_date(now),
        time_str=now.strftime("%H:%M"),
        total_count=raw.get("total_count", 0),
        section=section,
        brief=brief,
        buffett=buffett,
        generated_at=raw.get("generated_at"),
    )


@app.route("/api/econ")
def api_econ():
    force = request.args.get("refresh") == "1"
    raw = news_collector.collect_news(force_refresh=force)
    section = us_econ_tracker.build_us_econ_section(raw.get("items", []))
    return jsonify(section)


@app.route("/api/brief")
def api_brief():
    force = request.args.get("refresh") == "1"
    raw = news_collector.collect_news(force_refresh=force)
    section = us_econ_tracker.build_us_econ_section(raw.get("items", []))
    econ_items = _collect_econ_items(section)
    brief = gemini_summarizer.generate_brief(econ_items, force_refresh=force)
    return jsonify(brief or {"error": "no_brief"})


@app.route("/api/refresh")
def api_refresh():
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
    print("US Economic Daily")
    print("=" * 60)
    print(f"  주소        : http://localhost:{config.PORT}")
    print(f"  강제갱신    : http://localhost:{config.PORT}/?refresh=1")
    has_key = bool(os.environ.get("GEMINI_API_KEY", "").strip())
    print(f"  Gemini API  : {'활성화' if has_key else '비활성화 (GEMINI_API_KEY 없음)'}")
    print("=" * 60)
    print("  종료하려면 Ctrl+C 를 누르세요.")
    print("=" * 60)
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
