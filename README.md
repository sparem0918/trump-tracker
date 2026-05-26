# Trump Impact Tracker

트럼프 행정부 정책 동향과 한국 관련주 영향을 자동으로 추적하는 도구입니다.
RSS 뉴스를 수집해서 10개 정책·산업 토픽(양자컴퓨터, 관세/무역, 반도체, 자동차, 조선, 원자력/에너지, 방산/우주, 암호화폐, AI/빅테크, 중국 견제)으로 자동 분류하고, 각 토픽마다 시장에서 통상 묶이는 한국 관련주를 함께 보여줍니다.

`economic-daily`(경제 데일리 메인 사이트)의 자매 도구입니다.

## 주요 기능

- 한국경제·매일경제·연합뉴스·조선비즈·이투데이·Google News에서 RSS 자동 수집
- "트럼프", "백악관", "美 행정부" 등 키워드로 트럼프 관련 뉴스만 필터링
- 10개 정책·산업 토픽으로 자동 분류
- 토픽별 한국 관련주 50여 개 매핑 (종목명·코드·시장 구분)
- 매일 자동 갱신되는 버핏 체크포인트 (테마주 매수 전 점검 가이드)
- 매수 전 점검 질문 10개
- GitHub Pages 정적 사이트로 무료 배포

## 로컬 실행

요구사항: Python 3.11.9 이상

1. 이 폴더에서 `run.bat` 더블클릭
2. 브라우저에서 `http://localhost:5001` 열기
3. R 키 또는 우상단 새로고침 버튼으로 강제 갱신

처음 실행 시 venv 생성 및 패키지 설치로 1~2분 걸립니다.

## 파일 구조

```
trump_tracker_app/
├── app.py                  # Flask 메인
├── build_static.py         # GitHub Pages 정적 빌더
├── config.py               # RSS 피드, 캐시, 서버 설정
├── trump_config.py         # 트럼프 키워드, 토픽, 관련주 사전
├── trump_tracker.py        # 필터링·분류·매핑 로직
├── news_collector.py       # RSS 병렬 수집
├── buffett_loader.py       # 버핏 원칙 MD 파서
├── requirements.txt
├── run.bat                 # Windows 로컬 실행
├── .gitignore
├── DEPLOY_GITHUB_PAGES.md  # 배포 가이드
├── .github/workflows/
│   └── build.yml           # 자동 빌드·배포
├── templates/
│   └── index.html
├── static/
│   └── style.css
└── data/
    └── buffett_investment_method_korean.md
```

## 커스터마이징

### 토픽 추가/수정
`trump_config.py` 의 `TRUMP_TOPICS` 사전 수정.

```python
TRUMP_TOPICS["바이오"] = {
    "icon": "✚",
    "keywords": ["FDA", "임상", "신약", "바이오"],
    "description": "FDA 정책 변화와 한국 바이오 영향",
}
```

### 관련주 변경
`TOPIC_STOCKS` 사전. 시장 테마 분류는 시간이 지나면 바뀌므로 분기에 한 번씩 점검.

### 시간 윈도우
`trump_config.py` 의 `TRUMP_NEWS_HOURS_WINDOW` (기본 168시간 = 7일).

### RSS 피드 추가
`config.py` 의 `RSS_FEEDS` 리스트.

## 배포

`DEPLOY_GITHUB_PAGES.md` 참조. 새 GitHub repo를 만들고 push하면 GitHub Actions가 자동 빌드·배포합니다.

## 면책

- 본 도구는 공개 RSS 기반 보조 정보 제공 목적이며 종목 추천이 아닙니다.
- 관련주 매핑은 작성 시점 시장 통상 분류이고 시점에 따라 변경됩니다.
- 투자 판단과 그 결과에 대한 책임은 전적으로 본인에게 있습니다.

## 버핏 원칙과의 관계

테마주는 단기 모멘텀이 강하지만, 매수는 다음 순서로 검증해야 합니다 (`data/buffett_investment_method_korean.md` 참조):

1. 사업 이해도 — 트럼프 정책 수혜만으로 사는 게 아니라 실제 매출 구조에서 관련 사업 비중 확인
2. 5년 매출·이익 추이 — 단발성 테마인지 구조적 수혜인지 구분
3. 부채 안정성 — 테마 상승 후 유상증자·CB 발행 이력 점검
4. 밸류에이션 — 급등 후 PER·PBR이 과열 구간인지 확인

페이지 하단 "테마주 매수 전 점검 질문 10개"가 이 검증을 돕습니다.
