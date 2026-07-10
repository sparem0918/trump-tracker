# -*- coding: utf-8 -*-
"""
미국 경제 데일리 - 메인 설정
- RSS 피드: 국제·마켓·증권 중심 (미국 경제 뉴스가 많이 들어오는 채널)
- 미국 경제 키워드/토픽/관련주는 us_econ_config.py 에 분리
"""

# ---------------------------------------------------------------
# 1. RSS 피드
# ---------------------------------------------------------------
RSS_FEEDS = [
    # --- 국제 (미국 거시·정책 핵심 채널) ---
    {"name": "한국경제 국제", "url": "https://rss.hankyung.com/feed/international.xml", "category": "글로벌"},
    {"name": "매일경제 국제", "url": "https://www.mk.co.kr/rss/30300018/", "category": "글로벌"},
    {"name": "연합뉴스 국제", "url": "https://www.yna.co.kr/rss/international.xml", "category": "글로벌"},

    # --- 경제·마켓 ---
    {"name": "한국경제 경제", "url": "https://rss.hankyung.com/feed/economy.xml", "category": "경제"},
    {"name": "연합뉴스 경제", "url": "https://www.yna.co.kr/rss/economy.xml", "category": "경제"},
    {"name": "매일경제 경제", "url": "https://www.mk.co.kr/rss/30100041/", "category": "경제"},

    # --- 증권·특징주 (관련주 동향) ---
    {"name": "한국경제 증권", "url": "https://rss.hankyung.com/feed/stock.xml", "category": "증시"},
    {"name": "매일경제 증권", "url": "https://www.mk.co.kr/rss/50200011/", "category": "증시"},
    {"name": "이투데이 증권", "url": "https://www.etoday.co.kr/rss/rss_section.xml?id=22", "category": "증시"},

    # --- 산업 ---
    {"name": "한국경제 산업", "url": "https://rss.hankyung.com/feed/industry.xml", "category": "산업"},
    {"name": "연합뉴스 산업", "url": "https://www.yna.co.kr/rss/industry.xml", "category": "산업"},
    {"name": "조선비즈",       "url": "https://biz.chosun.com/site/data/rss/rss.xml", "category": "산업"},

    # --- 영문 (Google News 검색 RSS: 미국 경제 중심) ---
    {
        "name": "Google News - US Economy",
        "url": "https://news.google.com/rss/search?q=fed+OR+inflation+OR+semiconductor+korea&hl=en-US&gl=US&ceid=US:en",
        "category": "글로벌",
    },
]

# ---------------------------------------------------------------
# 2. 기본 동작 설정
# ---------------------------------------------------------------
CACHE_TTL_MINUTES = 30
NEWS_HOURS_WINDOW = 168  # 7일
MAX_NEWS_PER_CATEGORY = 10

HOST = "0.0.0.0"
PORT = 5001
DEBUG = False
