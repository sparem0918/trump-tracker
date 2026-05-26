# GitHub Pages 배포 가이드

`economic-daily` 배포 때 했던 과정과 거의 동일합니다. 새 repo만 하나 더 만들면 됩니다.

## 1. 새 GitHub repo 생성

브라우저에서 GitHub.com 로그인 후:

1. 우상단 `+` 아이콘 → **New repository** 클릭
2. 다음과 같이 입력:
   - **Repository name**: `trump-tracker` (또는 원하는 이름)
   - **Description**: `Trump Impact Tracker - 트럼프 정책 영향 추적`
   - **Public** 선택 (Pages 무료 사용 위해)
   - **README, .gitignore, license 추가 체크박스는 모두 비워두기** (충돌 방지)
3. **Create repository** 클릭

생성 후 화면에 보이는 repo URL을 메모하세요. 보통:
```
https://github.com/sparem0918/trump-tracker.git
```

## 2. 로컬에서 git 초기화 및 push

`trump_tracker_app` 폴더의 압축을 푼 위치에서 cmd를 열거나, 폴더 안에서 Shift+우클릭 → "여기에 PowerShell/터미널 열기".

> cmd가 폴더 안에 열렸는지 확인하세요. 프롬프트 마지막이 `...\trump_tracker_app>` 처럼 보이면 정상.

```cmd
git init
git add .
git commit -m "Initial commit: Trump Impact Tracker"
git branch -M main
git remote add origin https://github.com/sparem0918/trump-tracker.git
git push -u origin main
```

마지막 명령 실행 시 GitHub 로그인 창이 뜨면 로그인하세요. (Personal Access Token 방식이면 토큰 사용)

> repo 이름을 다르게 지었다면 위 `trump-tracker.git` 부분만 본인 이름으로 바꿔주세요.

## 3. GitHub Pages 활성화

`git push` 직후 GitHub Actions가 자동 실행되어 `gh-pages` 브랜치를 생성합니다. 약 2분 후:

1. 본인 repo 페이지 (`https://github.com/sparem0918/trump-tracker`) 접속
2. 상단 **Settings** 탭 클릭
3. 좌측 메뉴에서 **Pages** 클릭
4. **Build and deployment** 섹션에서:
   - **Source**: `Deploy from a branch` 선택
   - **Branch**: `gh-pages` 선택, 폴더는 `/ (root)` 선택
   - **Save** 클릭
5. 잠시 후 페이지 상단에 다음과 같이 표시됨:
   ```
   Your site is live at https://sparem0918.github.io/trump-tracker/
   ```

## 4. 동작 확인

위 URL로 브라우저 접속. 정상 작동하면 다음이 보입니다:

- 상단 **"트럼프 임팩트 트래커"** 큰 제목
- 요약 스트립 (관련 뉴스 건수, 활성 토픽 수 등)
- **JUMP TO** 토픽 빠른 이동 칩
- 토픽별 카드 (양자컴퓨터, 관세/무역, 반도체 등 활성 토픽만)
- 각 카드에 뉴스 리스트 + 한국 관련주 카드
- 하단 **버핏 체크포인트** + **매수 전 점검 질문**

## 5. 자동 갱신

워크플로 설정상:
- main 브랜치에 push할 때마다 빌드
- 매시간 정각(KST 기준) 자동 빌드 → RSS 최신 뉴스 반영

수동 빌드를 원하면 GitHub repo의 **Actions** 탭 → 좌측 "Build and Deploy Trump Tracker" → **Run workflow** 클릭.

## 6. 흔한 문제 해결

### "remote: Permission denied" 오류
GitHub Personal Access Token이 필요할 수 있습니다.
1. GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. **Generate new token (classic)** 클릭
3. 권한에 `repo` 체크
4. 생성된 토큰을 비밀번호 자리에 사용

### 빌드 실패 (Actions에서 빨간 X)
Actions 탭에서 실패한 워크플로 클릭 → 빨간 줄 로그 확인.
가장 흔한 원인:
- `[빌드 중단] 수집된 뉴스가 0건` → RSS 일시 장애 (다음 정각에 재시도)
- 모듈 import 에러 → 코드 문법 오류

### 사이트가 안 보임 (404)
- Pages 설정에서 Branch가 `gh-pages`인지 확인
- 빌드 후 3~5분 정도 CDN 캐시 반영 시간 필요
- 브라우저 강제 새로고침: Ctrl+Shift+R

### 트럼프 섹션이 비어 있음
RSS에서 트럼프 키워드 포함 뉴스를 못 찾은 경우. `trump_config.py` 에서:
```python
TRUMP_NEWS_HOURS_WINDOW = 168  # 이미 7일로 설정됨
```
이걸 더 늘리거나, 한국경제 정치·국제 같은 RSS가 살아 있는지 확인.

## 7. 두 사이트 운영 비교

| 항목 | economic-daily | trump-tracker |
|---|---|---|
| URL | `sparem0918.github.io/economic-daily/` | `sparem0918.github.io/trump-tracker/` |
| 포커스 | 일반 경제 뉴스 + 헤드라인 | 트럼프 정책 영향 + 관련주 |
| RSS | 경제·산업·증권 중심 | 정치·국제·증권 중심 |
| 빌드 주기 | (기존 설정 따름) | 매시간 정각 + push 시 |
| 코드 베이스 | 독립 | 독립 (코드 분리됨) |

두 사이트는 완전히 독립적으로 운영됩니다. 한쪽 수정이 다른 쪽에 영향을 주지 않습니다.
