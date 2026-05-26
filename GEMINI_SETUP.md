# Gemini API 키 설정 가이드

Gemini 종합 요약 기능을 사용하려면 무료 API 키가 필요합니다.

## 1. API 키 발급 (3분)

1. 브라우저로 [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) 접속
2. 본인 Google 계정으로 로그인
3. **Create API key** 버튼 클릭
4. 기존 Google Cloud 프로젝트가 없으면 새로 생성됨 (자동)
5. 발급된 키(`AIza...` 로 시작하는 긴 문자열) **복사해서 안전하게 보관**

> ⚠️ 키는 한 번 발급 후에도 페이지에서 다시 볼 수 있지만, 노출되면 즉시 폐기하고 재발급하세요.
> 절대 GitHub repo에 평문으로 커밋하지 마세요.

## 2. 무료 티어 제한 (참고)

| 항목 | 제한 |
|---|---|
| 모델 | gemini-2.5-flash (기본), gemini-2.0-flash 등 |
| RPM(분당 요청) | 무료: 15 RPM |
| RPD(일당 요청) | 무료: 1,500 RPD |
| 토큰 | 모델별 상이 |

이 프로젝트는:
- 빌드당 1회만 호출 (1시간 캐시)
- 매 시간 정각 자동 빌드 + push 시 빌드
- 하루 최대 ~30회 호출 예상

따라서 **무료 티어로 충분**합니다.

## 3. 로컬 테스트 (선택)

`run.bat` 실행 전 cmd에서 환경변수 설정:

```cmd
set GEMINI_API_KEY=AIzaSy...본인_키...
run.bat
```

또는 시스템 환경변수에 영구 등록:
1. Windows 설정 → 시스템 → 정보 → "고급 시스템 설정"
2. 환경 변수 → 사용자 변수에 **새로 만들기**
3. 변수 이름: `GEMINI_API_KEY`
4. 변수 값: 발급받은 키

설정 후 `run.bat` 실행하면 콘솔에 다음이 출력됩니다:
```
Gemini API : 활성화
```

브라우저에서 `http://localhost:5001` 접속 → 마스트헤드 바로 아래에 파란색 강조선의 **DAILY BRIEF** 섹션이 보이면 성공.

API 키 없이도 사이트 자체는 정상 작동합니다. Gemini 섹션만 자동으로 숨겨집니다.

## 4. GitHub Actions Secrets 설정 (배포용)

GitHub Pages 자동 빌드 시에도 Gemini를 사용하려면 repo에 secret 등록이 필요합니다.

1. 본인 repo 페이지(`https://github.com/sparem0918/trump-tracker`) 접속
2. 상단 **Settings** 탭
3. 좌측 메뉴 **Secrets and variables** → **Actions** 클릭
4. 우상단 **New repository secret** 클릭
5. 입력:
   - **Name**: `GEMINI_API_KEY`
   - **Secret**: 발급받은 키(`AIza...`) 붙여넣기
6. **Add secret** 클릭

설정 후 다음 빌드부터 Gemini 요약이 사이트에 표시됩니다.

> 한번 등록한 secret 값은 GitHub 측에서도 다시 볼 수 없습니다 (보안). 값을 분실하면 새 키 발급 후 secret을 업데이트하세요.

### 모델 변경 (선택)

기본 모델은 `gemini-2.5-flash`입니다. 다른 모델을 쓰고 싶으면:

1. Secrets 페이지에서 상단 **Variables** 탭 클릭
2. **New repository variable**:
   - **Name**: `GEMINI_MODEL`
   - **Value**: `gemini-2.0-flash` (또는 다른 모델명)

추천 모델:
- `gemini-2.5-flash` (기본) — 균형 잡힌 성능/비용
- `gemini-2.0-flash` — 가장 저렴하고 빠름
- `gemini-2.5-pro` — 가장 정교한 분석 (비용 높음, 무료 티어 제한 더 빡빡)

## 5. 동작 확인

GitHub Actions secret 등록 후:

1. repo의 **Actions** 탭 → 좌측 **Build and Deploy Trump Tracker**
2. 우상단 **Run workflow** 클릭 → **Run workflow** 버튼
3. 약 2-3분 후 빌드 완료
4. 사이트 강제 새로고침(Ctrl+Shift+R)
5. 마스트헤드 아래에 **DAILY BRIEF** 섹션이 나타나면 성공

빌드 로그에서 다음 메시지가 보이면 정상:
```
[Gemini] 종합 요약 생성 중... (52건, model=gemini-2.5-flash)
[Gemini] 요약 완료: 트럼프 2기 행정부는 양자컴퓨팅·반도체 등...
```

## 6. 문제 해결

### "GEMINI_API_KEY 환경변수가 없습니다" 메시지
- Secret 이름이 정확히 `GEMINI_API_KEY`인지 (대소문자 구분)
- Secret을 **Actions** secret으로 등록했는지 (Codespaces 또는 Dependabot이 아님)
- 등록 후 새로 빌드를 트리거했는지

### HTTP 400 오류
- 키가 유효한지 [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) 에서 확인
- 키 앞뒤 공백이 없는지

### HTTP 429 오류 (Rate Limit)
- 무료 티어 일 한도 초과. 다음 날 다시 시도하거나 모델을 변경.

### JSON 파싱 오류
- 매우 드물게 Gemini가 JSON 형식 어긋난 응답을 줄 때 발생
- 다음 빌드(1시간 후 정각)에 자동 재시도
- 또는 Actions에서 수동 재실행

### Brief 섹션이 안 보임
- 트럼프 관련 뉴스가 0건이면 Brief도 생성 안 됨 (입력 데이터 없음)
- `trump_config.py` 의 `TRUMP_NEWS_HOURS_WINDOW` 가 168(7일)인지 확인
- 빌드 로그에서 `[Gemini]` 줄을 찾아 어디서 멈췄는지 확인

## 7. 비용 관리 팁

무료 티어를 초과해서 유료 전환할 가능성은 거의 없지만, 안전 장치로:

1. Google Cloud Console → Billing → 예산 알림(Budget Alert) 설정
2. 월 $1 예산 + 50%/100% 알림 등록
3. 예상 외 호출이 늘면 즉시 알림

또는 빌드 주기를 매 시간 → 매 3시간으로 변경하려면 `.github/workflows/build.yml` 의:
```yaml
- cron: "0 * * * *"  # 매시간
```
를 다음으로 변경:
```yaml
- cron: "0 */3 * * *"  # 매 3시간
```
