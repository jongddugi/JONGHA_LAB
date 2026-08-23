# JONGHA_LAB
# YouTube 강의 요약기 (개인 복습용)

공개 유튜브 강의 URL 하나를 넣으면 Gemini API가 영상을 분석해서
개인 복습용 학습 노트(JSON + Markdown)를 만들어주는 파이썬 프로젝트입니다.
영상을 다운로드하지 않고 URL만 Gemini API에 전달합니다.

## 저작권 주의사항

1. 공개(public) 유튜브 영상만 지원됩니다. 비공개/일부공개 영상은 안 됩니다.
2. 무료 티어는 하루 최대 8시간 분량까지만 처리 가능합니다.
3. 본인이 시청할 권리가 있는 공개 강의 영상에만 사용하세요.
4. 결과물(요약 JSON/Markdown)은 개인 복습용으로만 사용하세요.
   공개 배포, 재판매, 강의 자료 대체 배포는 저작권 문제가 될 수 있습니다.
5. Structured Output은 형식만 보장하며 요약 내용의 사실 정확성을 보장하지 않습니다.

## 폴더 구조

youtube_lecture_summarizer/
  main.py             실행 진입점
  config.py           .env 로드 + 설정값
  models.py           Pydantic 데이터 모델
  gemini_client.py    Gemini API 호출 전용 클래스
  summarizer.py       요청+검증+재시도 흐름
  exporters.py        JSON/Markdown 저장 클래스
  utils.py            공통 함수
  requirements.txt    필요한 패키지 목록
  .env.example        API 키/URL 설정 예시
  .gitignore          git에 올리지 않을 파일 목록
  output/             결과 파일 저장 폴더 (git에는 올라가지 않음)

## 설치 및 실행 방법

1. 터미널에서 이 폴더로 이동한 뒤 가상환경을 만듭니다: python -m venv venv
2. 가상환경을 활성화합니다.
   - macOS/Linux: source venv/bin/activate
   - Windows(PowerShell): venv\Scripts\Activate.ps1
   - Windows(명령 프롬프트): venv\Scripts\activate.bat
   활성화되면 터미널 프롬프트 앞에 (venv)가 붙습니다.
3. pip install -r requirements.txt 로 패키지를 설치합니다.
4. .gitignore를 만들어서 .env가 git에 올라가지 않게 합니다.
5. .env.example을 .env로 복사합니다.
6. .env 파일에 GEMINI_API_KEY와 URL_PATH(요약할 공개 유튜브 강의 URL)를 채웁니다.
7. python main.py 를 실행합니다.
8. 실행이 끝나면 output/lecture_summary.json과 output/lecture_summary.md가 생성됩니다.
9. 작업을 마치면 deactivate 라고 입력해서 가상환경을 비활성화합니다.

## 주의

.env 파일에는 API 키와 URL_PATH가 들어있으므로 절대 git에 커밋하지 말고,
.gitignore에 반드시 포함하세요.