# trump-tracker → 미국 경제 데일리 전환 가이드

기존 `trump-tracker` repo를 그대로 사용하면서 내용만 미국 경제 데일리로 교체합니다.
GitHub Pages 설정, GEMINI_API_KEY secret, Actions 워크플로 구조는 모두 그대로 유지됩니다.

## 1. 변경 요약

| 구분 | 파일 | 처리 |
|---|---|---|
| 🗑 삭제 | `trump_config.py` | 더 이상 사용 안 함 |
| 🗑 삭제 | `trump_tracker.py` | 더 이상 사용 안 함 |
| 🆕 신규 | `us_econ_config.py` | 거시 5개 + 산업 8개 토픽, 관련주 43종목 |
| 🆕 신규 | `us_econ_tracker.py` | 거시/산업 이원화 분류 로직 |
| 🆕 신규 | `MIGRATION.md` | 이 파일 |
| 📝 교체 | `config.py` | RSS에 경제·마켓 피드 보강 |
| 📝 교체 | `app.py` | us_econ_tracker 사용으로 변경 |
| 📝 교체 | `build_static.py` | api/econ.json 생성 |
| 📝 교체 | `gemini_summarizer.py` | 미국 경제 분석 프롬프트 |
| 📝 교체 | `templates/index.html` | 거시/산업 이원화 레이아웃 |
| 📝 교체 | `static/style.css` | 화이트 배경 클린 디자인 |
| 📝 교체 | `.github/workflows/build.yml` | 워크플로 이름만 변경 |
| ✅ 유지 | `news_collector.py`, `buffett_loader.py`, `requirements.txt`, `run.bat`, `.gitignore`, `data/` | 변경 없음 (zip에 포함되어 있으니 그냥 덮어써도 무방) |

## 2. 적용 절차 (5분)

### (1) 파일 교체

로컬 `trump-tracker` 폴더(예: `Desktop\trump_tracker_app` 또는 clone 폴더)에서:

1. **삭제**: `trump_config.py`, `trump_tracker.py` 두 파일 삭제
2. **복사**: zip 압축 풀고 나온 모든 파일을 폴더에 붙여넣기 (덮어쓰기 허용)

### (2) git 반영

폴더에서 cmd 열고:

```cmd
git add -A
git commit -m "Migrate to US Economic Daily"
git push
```

> `git add -A` 는 삭제된 파일까지 함께 반영합니다 (일반 `git add .` 과의 차이).

### (3) 확인 (3분 후)

- GitHub Actions 탭에서 "Build and Deploy US Economic Daily" 워크플로 초록 체크 확인
- 사이트 접속 후 **Ctrl+Shift+R** 강제 새로고침
- 흰 배경의 "미국 경제 데일리" 페이지가 보이면 성공

## 3. 새 구조 설명

### 거시경제 (MACRO, 파란색) — 한국 영향 코멘트
| 토픽 | 내용 |
|---|---|
| 통화정책·금리 | 연준 FOMC·기준금리 → 환율·외국인 수급 |
| 물가·인플레이션 | CPI·PCE → 금리 경로·원화 |
| 고용·경기 | 비농업·실업률 → 경기 사이클 |
| 유가·원자재 | WTI·OPEC → 무역수지·물가 |
| 달러·환율 | 달러인덱스·원달러 → 수출 경쟁력 |

각 거시 토픽에는 관련주 대신 **한국 영향 해설 코멘트**가 표시됩니다.

### 산업·섹터 (SECTOR, 빨간색) — 한국 관련주
| 토픽 | 주요 관련주 |
|---|---|
| 반도체 | 삼성전자, SK하이닉스, 한미반도체, 이오테크닉스, HPSP, 리노공업 |
| AI·빅테크 | SK하이닉스, 네이버, 더존비즈온 등 |
| 자동차·2차전지 | 현대차, 기아, LG에너지솔루션, 에코프로비엠 등 |
| 조선·해운 | HD현대중공업, 한화오션, 삼성중공업, HMM 등 |
| 방산·우주 | 한화에어로스페이스, 현대로템, LIG넥스원 등 |
| 원전·전력기기 | 두산에너빌리티, HD현대일렉트릭, 효성중공업, 제룡전기 등 |
| 바이오·헬스케어 | 삼성바이오로직스, 셀트리온, 알테오젠 등 |
| 무역·관세 | 삼성전자, 현대차, 포스코홀딩스 등 |

## 4. 커스터마이징

모든 토픽·키워드·관련주는 `us_econ_config.py` 한 파일에서 관리합니다.

### 토픽 추가
```python
US_ECON_TOPICS["암호화폐"] = {
    "kind": "sector",
    "icon": "₿",
    "keywords": ["비트코인", "이더리움", "SEC", "가상자산"],
    "description": "미국 크립토 규제와 한국 가상자산 시장",
}
TOPIC_STOCKS["암호화폐"] = [
    {"name": "우리기술투자", "code": "041190", "market": "KOSDAQ", "note": "두나무 지분"},
]
```

### 거시 코멘트 수정
각 macro 토픽의 `kr_comment` 문자열을 직접 편집하면 됩니다.

### 분류 우선순위
`US_ECON_TOPICS` 사전의 **정의 순서 = 분류 우선순위**입니다.
하나의 뉴스가 여러 토픽에 매칭되면 위에 정의된 토픽에 배치됩니다.
구체적 토픽을 위에, 포괄적 토픽(무역·관세 등)을 아래에 두세요.

## 5. repo 이름 변경 (선택)

repo 이름이 여전히 `trump-tracker` 인 게 어색하면:

1. GitHub repo → Settings → General → Repository name 을 `us-econ-daily` 등으로 변경
2. 로컬에서 remote URL 업데이트:
   ```cmd
   git remote set-url origin https://github.com/sparem0918/us-econ-daily.git
   ```
3. 사이트 URL도 자동으로 `sparem0918.github.io/us-econ-daily/` 로 바뀝니다

이름을 유지해도 기능에는 아무 문제 없습니다.

## 6. 문제 해결

**페이지가 안 바뀜** → Ctrl+Shift+R 강제 새로고침. CDN 캐시 반영에 3~5분 걸릴 수 있음.

**빌드 실패** → Actions 로그에서 `ModuleNotFoundError: trump_config` 가 보이면 옛 파일 참조가 남은 것. `app.py` 와 `build_static.py` 가 새 버전으로 교체됐는지 확인.

**Gemini 요약 안 나옴** → Secret은 그대로 유효합니다. 빌드 로그에서 `[Gemini]` 메시지 확인.

**특정 토픽이 계속 비어 있음** → 해당 토픽 키워드가 실제 뉴스 표현과 맞는지 `us_econ_config.py` 에서 점검. 뉴스 제목을 몇 개 보고 자주 쓰이는 단어를 키워드에 추가.
