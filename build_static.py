# -*- coding: utf-8 -*-
"""
정적 사이트 빌더 (GitHub Pages 배포용) - 미국 경제 데일리
"""
import os
import sys
import shutil
import json
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app
import news_collector

OUTPUT_DIR = "site"


def ensure_clean_output():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "static"), exist_ok=True)


def copy_static_files():
    src = "static"
    dst = os.path.join(OUTPUT_DIR, "static")
    if os.path.exists(src):
        for fname in os.listdir(src):
            shutil.copy(os.path.join(src, fname), os.path.join(dst, fname))
            print(f"  복사: static/{fname}")


def rewrite_paths_for_static(html):
    import re
    html = html.replace('href="/static/', 'href="static/')
    html = html.replace('src="/static/', 'src="static/')
    html = re.sub(
        r"""window\.location\.href\s*=\s*['"]/\?refresh=1['"]""",
        "window.location.reload()",
        html,
    )
    return html


def add_build_meta(html):
    now_kst = datetime.now(timezone(timedelta(hours=9)))
    meta = (
        f"\n<!-- Built at {now_kst.isoformat()} | "
        f"US Economic Daily | Static build for GitHub Pages -->\n"
    )
    return html + meta


def build_index_html():
    raw = news_collector.collect_news(force_refresh=True)
    if raw.get("total_count", 0) == 0:
        print("=" * 60)
        print("[빌드 중단] 수집된 뉴스가 0건입니다.")
        print("=" * 60)
        sys.exit(1)

    with app.app.test_client() as client:
        resp = client.get("/?refresh=1")
        if resp.status_code != 200:
            print(f"[오류] HTTP {resp.status_code}")
            sys.exit(1)
        html = resp.get_data(as_text=True)

    html = rewrite_paths_for_static(html)
    html = add_build_meta(html)

    out_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  생성: index.html ({len(html):,} 자, 수집 뉴스 {raw['total_count']}건)")


def build_api_json():
    with app.app.test_client() as client:
        resp = client.get("/api/econ")
        if resp.status_code != 200:
            return
        data = resp.get_json()

    api_dir = os.path.join(OUTPUT_DIR, "api")
    os.makedirs(api_dir, exist_ok=True)
    out_path = os.path.join(api_dir, "econ.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"  생성: api/econ.json (미국 경제 {data.get('total_count', 0)}건)")


def create_nojekyll():
    with open(os.path.join(OUTPUT_DIR, ".nojekyll"), "w") as f:
        pass
    print(f"  생성: .nojekyll")


def create_robots_txt():
    with open(os.path.join(OUTPUT_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\n")
    print(f"  생성: robots.txt")


def main():
    print("=" * 60)
    print("US Economic Daily - Static Site Builder")
    print("=" * 60)
    ensure_clean_output()
    copy_static_files()
    build_index_html()
    build_api_json()
    create_nojekyll()
    create_robots_txt()
    print("=" * 60)
    print(f"[빌드 성공] 출력 디렉터리: {OUTPUT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
