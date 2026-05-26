# -*- coding: utf-8 -*-
"""
트럼프 임팩트 트래커 - 메인 설정
- RSS 피드: 트럼프·정책·국제 뉴스가 많이 들어오는 채널 중심
- 일반 경제 RSS도 일부 포함 (산업·증권 영향 파악용)
- 트럼프 키워드/토픽/관련주는 trump_config.py 에 분리
"""

# ---------------------------------------------------------------
# 1. RSS 피드
# ---------------------------------------------------------------
# 트럼프 관련 뉴스가 자주 들어오는 한국 매체의 국제·정치·증권 카테고리
# + 기본 경제 뉴스 일부 (산업 영향 파악)
RSS_FEEDS = [
    # --- 국제·정치 (트럼프 관련 핵심 채널) ---
    {"name": "한국경제 국제", "url": "https://rss.hankyung.com/feed/international.xml", "category": "글로벌"},
    {"name": "한국경제 정치", "url": "https://rss.hankyung.com/feed/politics.xml", "category": "글로벌"},
    {"name": "매일경제 국제", "url": "https://www.mk.co.kr/rss/30300018/", "category": "글로벌"},
    {"name": "연합뉴스 국제", "url": "https://www.yna.co.kr/rss/international.xml", "category": "글로벌"},
    {"name": "연합뉴스 정치", "url": "https://www.yna.co.kr/rss/politics.xml", "category": "글로벌"},

    # --- 증권·특징주 (관련주 동향 파악) ---
    {"name": "한국경제 증권", "url": "https://rss.hankyung.com/feed/stock.xml", "category": "증시"},
    {"name": "매일경제 증권", "url": "https://www.mk.co.kr/rss/50200011/", "category": "증시"},
    {"name": "이투데이 증권", "url": "https://www.etoday.co.kr/rss/rss_section.xml?id=22", "category": "증시"},

    # --- 산업 (반도체·자동차·조선 등 영향 파악) ---
    {"name": "한국경제 산업", "url": "https://rss.hankyung.com/feed/industry.xml", "category": "산업"},
    {"name": "연합뉴스 산업", "url": "https://www.yna.co.kr/rss/industry.xml", "category": "산업"},
    {"name": "조선비즈",       "url": "https://biz.chosun.com/site/data/rss/rss.xml", "category": "산업"},

    # --- 영문 (Google News 검색 기반 RSS) ---
    {
        "name": "Google News - Trump Korea",
        "url": "https://news.google.com/rss/search?q=trump+korea+OR+semiconductor+OR+tariff&hl=en-US&gl=US&ceid=US:en",
        "category": "글로벌",
    },
]

# ---------------------------------------------------------------
# 2. 기본 동작 설정
# ---------------------------------------------------------------
# 캐시 유효 시간(분) - 로컬 실행 시
CACHE_TTL_MINUTES = 30
# 수집 후 며칠치 뉴스를 유지할지 (수집기 내부 용도)
NEWS_HOURS_WINDOW = 168  # 7일
# 카테고리당 최대 뉴스 수
MAX_NEWS_PER_CATEGORY = 10

# 서버 설정 (로컬 실행 시)
HOST = "0.0.0.0"
PORT = 5001  # economic-daily(5000) 와 충돌 방지
DEBUG = False
