# -*- coding: utf-8 -*-
"""
트럼프 임팩트 트래커 - Flask 메인
- 메인 페이지: 트럼프 영향 토픽별 분류 + 관련주
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


@app.route("/")
def index():
    """메인: 트럼프 임팩트 트래커"""
    force = request.args.get("refresh") == "1"
    raw = news_collector.collect_news(force_refresh=force)
    items = raw.get("items", [])

    trump_section = trump_tracker.build_trump_section(items)
    buffett = buffett_loader.get_buffett_context()

    now = _kst_now()

    return render_template(
        "index.html",
        date_str=format_korean_date(now),
        time_str=now.strftime("%H:%M"),
        total_count=raw.get("total_count", 0),
        trump_section=trump_section,
        buffett=buffett,
        generated_at=raw.get("generated_at"),
        topics_meta=trump_config.TRUMP_TOPICS,  # 토픽 전체 목록 (TOC용)
    )


@app.route("/api/trump")
def api_trump():
    """JSON API: 트럼프 섹션 데이터"""
    force = request.args.get("refresh") == "1"
    raw = news_collector.collect_news(force_refresh=force)
    items = raw.get("items", [])
    section = trump_tracker.build_trump_section(items)
    return jsonify(section)


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
    return jsonify({"status": "ok", "time": _kst_now().isoformat()})


if __name__ == "__main__":
    print("=" * 60)
    print("Trump Impact Tracker")
    print("=" * 60)
    print(f"  주소     : http://localhost:{config.PORT}")
    print(f"  로컬망   : http://<PC-IP>:{config.PORT}")
    print(f"  강제갱신 : http://localhost:{config.PORT}/?refresh=1")
    print("=" * 60)
    print("  종료하려면 Ctrl+C 를 누르세요.")
    print("=" * 60)
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
