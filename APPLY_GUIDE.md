# Gemini Brief 패치 적용 가이드

기존 `trump_tracker_app` 프로젝트에 Gemini 종합 요약 기능을 추가하는 패치입니다.

## 변경 사항 (7개 파일)

| 분류 | 파일 | 비고 |
|---|---|---|
| 🆕 신규 | `gemini_summarizer.py` | Gemini API 호출 모듈 |
| 🆕 신규 | `GEMINI_SETUP.md` | API 키 설정 가이드 |
| 📝 수정 | `app.py` | Gemini brief 생성·전달 |
| 📝 수정 | `templates/index.html` | DAILY BRIEF 섹션 추가 |
| 📝 수정 | `static/style.css` | brief 섹션 스타일 추가 |
| 📝 수정 | `.github/workflows/build.yml` | GEMINI_API_KEY 환경변수 |
| 📝 수정 | `APPLY_GUIDE.md` | 이 파일 |

## 적용 절차 (5분)

### 1. 파일 복사·덮어쓰기

zip을 풀어서 `trump_tracker_app` 폴더의 같은 위치에 7개 파일을 복사. 신규 파일은 추가되고, 기존 5개 파일은 덮어쓰기.

```
trump_tracker_app/
├── gemini_summarizer.py          ← 신규
├── GEMINI_SETUP.md               ← 신규
├── APPLY_GUIDE.md                ← 신규 (이 파일)
├── app.py                        ← 덮어쓰기
├── .github/workflows/build.yml   ← 덮어쓰기
├── templates/
│   └── index.html                ← 덮어쓰기
└── static/
    └── style.css                 ← 덮어쓰기
```

> 다른 파일들(`trump_config.py`, `trump_tracker.py`, `news_collector.py`, `buffett_loader.py`, `config.py`, `build_static.py`, `requirements.txt`, `run.bat`, `data/buffett_investment_method_korean.md`)은 **변경 없음** 그대로 둡니다.

### 2. Gemini API 키 발급 및 설정

`GEMINI_SETUP.md` 참조해서 다음을 진행:

1. [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) 에서 무료 키 발급
2. GitHub repo (`trump-tracker`) → Settings → Secrets and variables → Actions
3. **New repository secret** 클릭
4. Name: `GEMINI_API_KEY`, Secret: 발급받은 키 붙여넣기
5. **Add secret** 클릭

### 3. push

`trump_tracker_app` 폴더에서 cmd 열고:

```cmd
git add .
git commit -m "Add Gemini AI brief section"
git push
```

### 4. 동작 확인

- 약 2-3분 후 GitHub Actions에서 빌드 완료 확인 (초록 체크)
- 브라우저에서 `https://sparem0918.github.io/trump-tracker/` 접속
- **Ctrl+Shift+R** 로 강제 새로고침
- 마스트헤드 ↓ **DAILY BRIEF** 파란색 강조선 섹션 ↓ 요약 스트립 ↓ JUMP TO ↓ 토픽들 순서로 표시되면 성공

## 로컬 테스트도 가능합니다

API 키를 환경변수로 설정 후 `run.bat` 실행:

```cmd
set GEMINI_API_KEY=AIzaSy...본인_키...
run.bat
```

콘솔에 `Gemini API : 활성화` 메시지가 보이면 정상.

## 빌드 로그 확인

GitHub Actions의 빌드 로그(`Build static site` 단계)에 다음 줄이 보이면 정상:

```
[Gemini] 종합 요약 생성 중... (52건, model=gemini-2.5-flash)
[Gemini] 요약 완료: 트럼프 2기 행정부는 양자컴퓨팅·반도체 등...
```

만약 다음 메시지가 보이면 secret 설정 확인:
```
[Gemini] GEMINI_API_KEY 환경변수가 없습니다. 요약 건너뜀.
```

## 동작 방식

1. RSS 수집 → 489건 같은 전체 뉴스 확보
2. `trump_tracker` 로 트럼프 키워드 필터링 → 52건
3. 토픽별 분류 (관세/무역 16건, 자동차 5건, …)
4. **이 시점에 분류된 트럼프 뉴스만** Gemini에 전달
5. Gemini가 정책 동향 + 한국 영향 종합 요약 생성
6. 1시간 캐시 (동일 뉴스 셋이면 재호출 안 함)
7. 페이지 상단에 표시

빌드 1회당 Gemini 호출 1회, 1시간 캐시 적용이라 무료 티어에 충분합니다.

## 비활성화하고 싶을 때

GitHub Secrets에서 `GEMINI_API_KEY`를 삭제하면 Brief 섹션이 자동으로 숨겨지고, 기존 페이지 형태로 돌아갑니다. 코드 수정 불필요.

## 트러블슈팅

상세한 문제 해결은 `GEMINI_SETUP.md` 6번 항목 참조.
