# convertN2C — 설계 문서 (Novel → Comic 데스크톱 앱)

> 상태: 기획 단계 (코드 미작성).
> **배포 형태: 웹이 아니라 Windows 데스크톱 EXE.**
> 스택: **Python 백엔드(FastAPI, 로컬 in-process) + React 프론트엔드(정적 빌드)**, **PyWebView + PyInstaller** 단일 exe 패키징.
> LLM **Claude (Anthropic)**, 이미지 생성 **외부 이미지 API**(Replicate/fal 등).
> 배포 범위 **타인 배포** — 각 사용자가 본인 API 키를 입력해 사용.

---

## 1. 제품 개요

프로젝트 단위로 캐릭터 설정·화풍·세계관·이전 스토리 맥락을 영속 저장하여, 소설을 회차별로 업로드해도 **일관된 화풍과 캐릭터**로 만화를 생성하는 **데스크톱 프로그램**.

핵심 가치:
- 장편 연재 대응 (회차 누적)
- 캐릭터·화풍의 영속성(Consistency)
- 다중 프로젝트 관리
- **설치형 단일 exe** — 서버 운영 없이 각자 PC에서 실행

배포 모델 함의:
- 중앙 서버 없음. 모든 데이터는 **사용자 PC 로컬**에 저장.
- Claude·이미지 API는 **사용자 본인 키**로 직접 호출(인터넷 필요). API 비용은 각 사용자 부담.
- 오프라인 불가(LLM·이미지 API 호출 시점에 인터넷 필요).

## 2. 유저 시나리오

0. **최초 실행** — 설정 화면에서 본인 Anthropic 키 + 이미지 API 키 입력 → OS 자격증명 저장소에 안전 저장.
1. **프로젝트 생성** — 그림체 스타일(로맨스 판타지풍 등) 지정 → 글로벌 스타일 에셋 고정.
2. **메모리 빌드** — 1화 업로드 → 등장인물 추출 → 참조 이미지 등록 → 글로벌 메모리 저장.
3. **이어하기** — 2화 업로드 → 1화의 캐릭터/스타일/줄거리를 기억한 상태에서 생성.

## 3. 기능 요구사항 (요약)

| ID | 기능 | 우선순위 |
|---|---|---|
| FR-0.0 | 설정 화면: API 키 입력·검증·로컬 저장 | High |
| FR-0.1 | 대시보드 / 다중 프로젝트 | High |
| FR-0.2 | 글로벌 스타일 에셋 고정 (스타일 프롬프트, 외부 API의 모델/LoRA 식별자) | High |
| FR-0.3 | 캐릭터 뱅크 (참조 이미지 + 특징, 프로젝트 귀속) | High |
| FR-0.4 | 스토리 컨텍스트 메모리 (회차 요약 → 다음 회차 콘티에 주입) | Medium |
| FR-1.1 | 회차(Episode) 단위 소설 업로드 | High |
| FR-1.2 | 신규/기존 인물 교차 검증 (AI 판별 + 유저 확인) | High |
| FR-2.1 | 메모리 기반 프롬프트 엔진 (스타일+캐릭터+컷 묘사 조립) | High |
| FR-2.2 | 대사·레이아웃 합성 (프로젝트별 폰트·말풍선) | Medium |

## 4. 시스템 아키텍처 (데스크톱)

전부 한 exe 안에서 동작. PyWebView 창이 React 정적 빌드를 띄우고, 같은 프로세스 안의 FastAPI(127.0.0.1 바인딩, 외부 노출 X)가 백엔드 역할. 외부 통신은 Claude API와 이미지 API뿐.

```
┌──────────────────────── convertN2C.exe (사용자 PC) ────────────────────────┐
│                                                                            │
│  ┌────────────────────┐        loopback         ┌───────────────────────┐  │
│  │ PyWebView 창        │ ───── 127.0.0.1 ──────▶ │ FastAPI (로컬, in-proc)│  │
│  │  React 정적 빌드 UI  │                         │  - 프로젝트/회차 API    │  │
│  └────────────────────┘                         │  - 메모리 빌더          │  │
│                                                 │  - 프롬프트 엔진        │  │
│                                                 └───┬───────────┬───────┘  │
│                                                     │           │          │
│   ┌──────────────┐   ┌─────────────────┐   ┌───────▼──┐   ┌────▼────────┐  │
│   │ SQLite       │   │ 로컬 벡터 저장소 │   │ 로컬 파일 │   │ 키 저장소    │  │
│   │ (프로젝트/회차)│  │ (캐릭터/요약 검색)│   │ (이미지)  │   │ OS Credential│ │
│   └──────────────┘   └─────────────────┘   └──────────┘   └─────────────┘  │
│                                                     │                       │
└─────────────────────────────────────────────────── │ ──────────────────────┘
                                                      │ HTTPS (사용자 키)
                              ┌───────────────────────┼──────────────────────┐
                              ▼                                               ▼
                     ┌────────────────┐                          ┌──────────────────┐
                     │ Claude (LLM)   │                          │ 외부 이미지 API   │
                     │ - 인물 추출/검증 │                          │ (Replicate/fal..)│
                     │ - 회차 요약     │                          │ - 패널 이미지 생성│
                     │ - 콘티 생성     │                          │ - 캐릭터 일관성   │
                     └────────────────┘                          │   (IP-Adapter 등)│
                                                                 └──────────────────┘
```

### 로컬 스토리지 배치

앱 데이터 루트: `%APPDATA%\convertN2C\` (Python `platformdirs`로 경로 결정). S3는 사용하지 않음.

- **관계형 DB**: SQLite 단일 파일 — Project / Episode / Panel / Character 메타.
- **벡터 저장소**: 로컬 임베디드. 후보 — `sqlite-vec`(SQLite 한 파일에 통합, 가장 단순·권장) / Chroma(embedded persistent) / FAISS. *미결.*
- **파일 저장소**: `…\convertN2C\projects\<project_id>\` 하위에 참조 이미지·생성 컷 보관.
- **키 저장소**: `keyring`(Windows Credential Manager) — 평문 설정 파일·exe 번들 금지.

### 데이터 모델 (초안)

- **Project**: `id`, `name`, `style_prompt`, `image_model_ref`(외부 API 모델/LoRA 식별자), `font/말풍선 설정`, `created_at`
- **Character** (프로젝트 귀속): `id`, `project_id`, `name`, `traits`(JSON), `ref_image_path`(로컬), `face_embedding`(벡터 저장소)
- **Episode**: `id`, `project_id`, `number`, `raw_text`, `summary`, `status`
- **Panel** (컷): `id`, `episode_id`, `order`, `prompt`, `image_path`(로컬), `dialogue`(JSON)
- **GlobalMemory**: 프로젝트별 — 캐릭터 뱅크 + 세계관 서술 + 누적 회차 요약 (프롬프트 캐시 대상)

## 5. 키·설정 관리 (데스크톱 핵심)

- 최초 실행 시 **본인 Anthropic 키 + (선택)Gemini 무료 키 + 이미지 API 키** 입력. exe에 어떤 키도 번들하지 않음.
- 저장: `keyring`으로 OS 자격증명 저장소(Windows Credential Manager). 평문 JSON 금지.
- 입력 직후 가벼운 호출(예: Claude `models.list` / 이미지 API ping)로 키 유효성 검증.
- 키 없음/만료 시 명확한 안내 + 설정 화면으로 유도. 비용은 사용자 부담임을 UI에 명시.
- 모든 외부 호출은 사용자 키로 사용자 PC에서 직접 발생 → 우리 쪽 프록시/서버 없음.

## 6. LLM 통합 설계 (제공자 추상화)

> 정확한 모델 ID·가격·API 동작은 [CLAUDE.md](../CLAUDE.md) 참조. 모든 LLM 호출은 `app/llm/` 의 단일 모듈을 경유하며, 키는 §5의 저장소에서 읽는다.

### 6.0 제공자 추상화 — Claude 기본 + Gemini 무료 토글

`LLMProvider` 인터페이스 뒤에 두 구현체를 둔다(구현은 P4):

- **Claude(Anthropic)** — 기본·고품질. 비용은 사용자 부담.
- **Gemini(Google) 무료 티어** — 설정의 "무료 버전 사용" 토글 시 사용. 무료 키 발급, 분당 요청 제한 있음.

```python
class LLMProvider(Protocol):
    def extract_characters(self, text: str, bank: CharacterBank) -> CharacterExtraction: ...
    def summarize_episode(self, text: str, context: GlobalMemory) -> str: ...
    def generate_storyboard(self, episode: Episode, memory: GlobalMemory) -> list[PanelDraft]: ...
```

**통일성에 미치는 영향(중요):** 프로젝트 기억은 *모델*이 아니라 *데이터*(글로벌 메모리를 매 회차 재주입)에서 나오므로, 무료 LLM으로 바꿔도 **기억 메커니즘은 유지**되고 텍스트 품질(추출 정확도·요약 충실도·콘티 표현력)만 점진적으로 하락한다. 시각적 일관성(얼굴/화풍)은 LLM이 아니라 §7 이미지 단계가 좌우한다.

**제공자별 차이(P4에서 흡수):** 프롬프트 캐싱·구조화 출력은 제공자마다 방식이 다르다(Claude=`cache_control`/`output_config.format`, Gemini=context caching/response schema). 인터페이스는 동일하게 유지하고 내부에서 매핑한다.

### 6.1 모델 선택 (역할별 — Claude 사용 시)

| 역할 | 모델 | 이유 |
|---|---|---|
| 콘티 생성, 캐릭터 일관성 추론 | `claude-opus-4-8` | 1M 컨텍스트, 최고 추론. 누적 줄거리 주입에 적합 |
| 회차 요약, 일반 추출 | `claude-sonnet-4-6` | 속도·비용 균형 |
| 신규/기존 인물 교차 검증(분류) | `claude-haiku-4-5` | 빠르고 저렴한 분류 작업 |

> 비용은 사용자 부담이므로, 설정에서 "품질↔비용" 프리셋(모델·effort 조절)을 제공하는 것을 검토.

### 6.2 프롬프트 캐싱 전략 (사용자 비용 절감 + 일관성)

회차마다 동일한 **글로벌 메모리**(스타일+캐릭터 뱅크+세계관+이전 회차 요약)를 system 프리픽스로 보내고 `cache_control` 적용. prefix-match 이므로 **고정 콘텐츠 앞, 변동(현재 회차 텍스트) 뒤**.

- 렌더 순서 `tools → system → messages`. system 마지막 블록 breakpoint로 tools+system 동시 캐시.
- 최소 캐시 프리픽스: Opus 4.8 = 4096 토큰(미만이면 조용히 캐시 안 됨).
- 연재 편집 세션 동안 재호출 잦음 → `ttl: "1h"` 검토.
- `datetime.now()`·UUID 등을 system 프리픽스에 넣지 말 것(캐시 무효화).
- 데스크톱 단일 사용자라 캐시는 본인 호출 사이에서만 재사용됨 — 그래도 회차 반복 생성/재시도에 효과적.

### 6.3 긴 컨텍스트

Opus 4.8 / Sonnet 4.6 모두 **1M 컨텍스트**. 원문이 아니라 **요약본 누적**으로 토큰 관리. 한계 접근 시 compaction(beta) 고려.

### 6.4 system 프롬프트

- 프로젝트 스타일·세계관 규칙은 system에 동결(캐시 보존).
- 회차별 변동 맥락은 `messages`에 주입. Opus 4.8은 대화 중간 `{"role":"system",...}` 메시지로 캐시 보존하며 주입 가능.

### 6.5 도구 / 구조화 출력

- **인물 추출·교차 검증**: `output_config.format`(JSON schema) → `{characters:[{name,is_new,traits,matched_character_id}]}` → 유저 확인 단계.
- **프롬프트 엔진**: `[스타일]+[캐릭터 뱅크]+[컷 묘사]` 최종 문자열 조립은 결정적 코드로(캐시·재현성).
- 긴/대량 출력은 streaming + `.get_final_message()`.
- 캐릭터 일관성 추론 등 복잡 작업엔 adaptive thinking(`thinking={"type":"adaptive"}`).

### 6.6 비동기/대량 처리

- 소설 파일 업로드: **Files API**(beta)로 업로드 후 `file_id` 재사용.
- 한 회차 다수 컷 프롬프트 일괄 생성: **Batches API**(50% 비용) — 지연 허용 시. 단, 데스크톱 UX상 진행률 표시되는 streaming이 보통 더 적합.

## 7. 이미지 생성 추상화

`ImageGenerator` 인터페이스 뒤에 **두 구현체**(LLM 제공자 추상화와 동일 패턴, 설정 토글로 전환):

- **Gemini 이미지 (기본·무료)** — `gemini-2.5-flash-image`(Nano Banana). 무료 하루 500장, LLM과 **같은 Gemini 키 재사용**(추가 발급 불필요). 캐릭터 뱅크의 **참조 이미지를 입력으로 주어** 일관성 유지. 상위 모델(`gemini-3-pro-image` 등)도 같은 키로 접근 가능하나 무료 티어 없음.
- **외부 API (Replicate/fal 등)** — SD + LoRA + IP-Adapter/InstantID로 화풍·얼굴을 더 정교하게 제어. 별도 키·과금.

키는 §5 저장소에서 로드.

```python
class ImageGenerator(Protocol):
    def register_character(self, project_id: str, ref_image: bytes) -> CharacterRef: ...
    def generate_panel(self, prompt: str, style: StyleAsset,
                       characters: list[CharacterRef]) -> bytes: ...
```

- 일관성 제어: 외부 API가 제공하는 IP-Adapter/InstantID·LoRA 기능에 의존(제공 기능에 종속됨을 문서화).
- 호출은 사용자 키로 직접. 생성 결과는 로컬 파일 저장소에 저장.
- 인터페이스를 유지하면 추후 로컬 GPU(SD)로 교체 가능.

> ⚠️ **무료 이미지 주의:** 캐릭터 얼굴·화풍의 시각적 통일성은 이 단계가 좌우한다. 무료 이미지 엔드포인트(예: Pollinations 등)는 IP-Adapter/LoRA 같은 일관성 제어를 제공하지 않는 경우가 많아 회차 간 얼굴이 달라질 위험이 크다. 진짜 무료이면서 일관성도 되는 선택지는 **로컬 GPU + SD**뿐(사용자 VRAM 필요). LLM 무료화(§6.0)와 달리 이미지 무료화는 통일성 리스크가 크므로, 1차 구현은 유료라도 일관성 기능을 제공하는 외부 API로 가고 무료 이미지는 별도 옵션으로 미룬다.

## 8. 패키징 & 배포

- **UI**: React를 **정적 빌드(SPA)** 로 산출 → PyWebView가 로드. (Next.js를 쓸 경우 `output: 'export'` 정적 익스포트, 또는 Vite+React가 더 가벼움 — *미결, Vite 권장*.)
- **백엔드**: FastAPI를 별도 서버 배포가 아니라 앱 프로세스 안에서 127.0.0.1 바인딩으로 기동(외부 미노출). PyWebView 창이 이 로컬 UI/엔드포인트에 연결.
- **패키징**: **PyInstaller** 로 단일 exe. React 정적 자산을 데이터로 포함.
- **런타임 의존성**: PyWebView는 Windows에서 Edge **WebView2 런타임** 필요(Win11 기본 포함, 부재 시 안내).
- **경로 주의**: PyInstaller 번들에서는 `__file__` 대신 `sys._MEIPASS` 기준으로 정적 자산 경로 해석.

## 9. 비기능 요구사항

- **일관성 품질**: 동일 프로젝트 1화↔5화 주인공 얼굴/화풍 체감 오차 < 10%.
- **로컬 스토리지**: 프로젝트별 참조 이미지·생성 컷을 앱 데이터 폴더에 체계적 관리(용량 표시·정리 기능 검토).
- **보안**: API 키는 OS 자격증명 저장소에만. 로그·메모리 파일·예외 메시지에 키 노출 금지.
- **비용 투명성**: 사용자 키로 과금되므로 호출 전/후 예상·실사용 토큰·이미지 수 표시 검토.
- **인터넷 의존**: 생성 단계는 온라인 필요. 오프라인 시 명확한 안내.

## 10. 결정된 사항 / 미결 사항

결정: 데스크톱 EXE / PyWebView+PyInstaller / Python(FastAPI 로컬)+React(Vite) / LLM=**Claude 기본 + Gemini 무료 토글**(제공자 추상화) / 이미지=외부 API(일관성 기능 제공) / 타인 배포·사용자 자기 키.
미결: 벡터 저장소 제품(sqlite-vec 권장) · 외부 이미지 API 공급자 · 무료 이미지 옵션 여부 · 자동 업데이트 방식.
