# CapCut 대안 — 영상 자동화 툴 전수 조사 (2026.06)

**CapCut(剪映)은 공개 API 없음** → 계정 로그인·자동 편집 불가.  
아래는 **API / MCP / 에이전트 연동 가능**하거나, **수동이지만 CapCut 대체**로 쓸 수 있는 도구 **전체 목록**.

---

## 한눈에 보기 — 카테고리별

| 카테고리 | 대표 | API | 에이전트 적합 | 합격닷컴 적합도 |
|----------|------|-----|---------------|-----------------|
| **편집 API (템플릿)** | JSON2Video, Creatomate, Shotstack | ✅ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **AI 인플루언서 훅** | D-ID, HeyGen, Tavus | ✅ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **UGC 숏폼 광고** | Nextify, Creatify, Kaloclip, Nouvel | ✅/플랫폼 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **에이전트 네이티브 API** | UGC Copilot, ReelsBuilder, JSON2Video MCP | ✅ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **AI 영상 생성 (I2V/T2V)** | Kling, Runway, Veo, Luma, Pika | ✅ | ⭐⭐⭐ | ⭐⭐ (움직임만) |
| **코드 퍼스트** | Remotion, MoviePy, FFmpeg, OpenMontage | ✅/CLI | ⭐⭐⭐⭐ | ⭐⭐ (셋업 무거움) |
| **After Effects 기반 API** | Plainly, Shakr | ✅ | ⭐⭐⭐ | ⭐⭐⭐ (AE 필요) |
| **SaaS 편집기 (수동)** | Canva, Descript, Kapwing, InVideo | 제한적/없음 | ⭐ | ⭐⭐ (손작업) |

---

## 1. 영상 편집 API — 템플릿 기반 (슬라이드쇼 X)

이미지+영상 클립+VO+자막+트랜지션을 **한 번에** 합성. CapCut이 하는 일을 API로.

| 툴 | API | MCP | TTS/자막 | 9:16 | 무료 | 월 시작 | 특징 |
|----|-----|-----|----------|------|------|---------|------|
| **JSON2Video** | ✅ REST | ✅ **공식 MCP** | ✅ 한국어 | ✅ | ~10분 | $49.95 | **Cursor 에이전트 1순위** |
| **Creatomate** | ✅ REST | ❌ | ✅ | ✅ | 50크레딧 | $41 | 비주얼 에디터+JSON, 4K |
| **Shotstack** | ✅ REST | ❌ | ❌ 별도 | ✅ | 10크레딧 | $39 | 개발자용 JSON 타임라인 |
| **Placid** | ✅ REST | ❌ | ❌ | ✅ | 제한 | $19 | 오버레이·워터마크·클립 병합 |
| **Plainly** | ✅ REST | ❌ | ❌ | ✅ | 트라이얼 | 문의 | **After Effects** 템플릿 렌더 |
| **Moovly** | ✅ REST | ❌ | ✅ | ✅ | 제한 | 문의 | 대량 데이터 기반 영상 |
| **Bannerbear** | ✅ REST | ❌ | ❌ | ✅ | 제한 | $49 | **이미지 특화**, 영상은 오버레이만 |
| **Shakr** | ✅/매니지드 | ❌ | ❌ | ✅ | ❌ | 문의 | 소셜 광고, AE 기반 |

### JSON2Video — 에이전트 연동 (추천 1순위)

- 공식 MCP: https://json2video.com/docs/v2/help-for-ai-agents/mcp-server
- 이미지 인서트 + 한국어 TTS + 자막 + 트랜지션 한 파이프라인
- 무료 ~600 credits (~10분) → V1~V4 테스트 가능

```json
// ~/.cursor/mcp.json
{
  "mcpServers": {
    "json2video": {
      "command": "npx",
      "args": ["-y", "@json2video/cli", "mcp"],
      "env": { "JSON2VIDEO_API_KEY": "YOUR_KEY" }
    }
  }
}
```

### Creatomate vs Shotstack

| | Creatomate | Shotstack |
|---|------------|-----------|
| 접근 | 드래그앤드롭 에디터 → JSON | JSON 직접 작성 |
| $99/월 분량 | ~700분 (720p) | ~500분 |
| 강점 | 디자이너+개발자 협업 | 인프라급 렌더 속도 |
| 약점 | 구독만 | 동적 길이 콘텐츠 까다로움 |

---

## 2. AI 인플루언서 / 말하는 사람 — 「요즘 AI ~~ 툴」 훅

레퍼런스 `1minute_sangse` / `DYoixpiKluI` 스타일의 **3초 훅**에 최적.

| 툴 | API | 한국어 | 사진→영상 | 월/API 시작 | 특징 |
|----|-----|--------|-----------|-------------|------|
| **D-ID** | ✅ **전 플랜** | ✅ | ✅ **1장** | ~$6 | 개발자 1순위, 립싱크, Talks API |
| **HeyGen** | ✅ Pay-as-you-go | ✅ 175+ | ✅ Instant Avatar | $1/분(720p) | 퀄리티 최고, Ad Maker |
| **Synthesia** | Enterprise만 | ✅ 140+ | ✅ | $22+ UI / API 별도 | 기업 L&D, SCORM |
| **Tavus** | ✅ | ✅ | ✅ | 문의 | 개인화 영상, API |
| **DeepBrain AI** | ✅ | ✅ | ✅ | 문의 | AI Studios, 한국계 |
| **Rephrase.ai** | ✅ | ✅ | ✅ | 문의 | 인도 기반, API |
| **Colossyan** | Enterprise | ✅ | ✅ | $27+ | 교육용 아바타 |
| **Elai.io** | ✅ | ✅ 75+ | ✅ | $23+ | URL→영상 |
| **Synthesys** | ✅ | ✅ | ✅ | $29+ | UGC 스타일 |

### D-ID 예시 (컨펌 `pmax_portrait_960x1200.png`)

```bash
POST https://api.d-id.com/talks
Authorization: Basic API_KEY
{
  "script": { "type": "text", "input": "요즘 취준생 사이에서 난리난 AI 자소서 툴 알아?" },
  "source_url": "https://.../pmax_portrait.png"
}
```

### HeyGen

- AI Ad Maker: https://www.heygen.com/ko-kr/tool/ai-ad-maker
- API: Pay-as-you-go, **$1 = 1분** (720p/1080p 표준)
- 2026.02~ 무료 API 크레딧 없음 → 크레딧 구매 필요

---

## 3. UGC / 숏폼 광고 특화 — 제품→릴스 원스톱

| 툴 | API | 한국어 | 입력 | 배치 | 특징 |
|----|-----|--------|------|------|------|
| **Nextify.ai** | ✅ | ✅ KO 사이트 | URL/이미지 | 50~500변형 | Sora2/Veo3.1, B-roll, 아바타 |
| **Kaloclip (칼로클립)** | 플랫폼 (틱톡 API) | ✅ **2026 한국 론칭** | 상품링크 | ✅ | 벤치마킹+훅+대량생성 |
| **Creatify.ai** | ✅ | ✅ | URL | ✅ | Meta/TikTok 직접 게시, Ad Cloner |
| **Nouvel** | ✅ REST | 자동감지 | 제품 URL 1~3개 | variantCount | UGC 스타일, 웹훅 |
| **Arcads** | ✅ | 영어 위주 | 스크립트 | ✅ | UGC AI actor |
| **Waymark** | ✅ | 영어 | 비즈니스 URL | ❌ | TV광고 스타일 |
| **Pictory** | ✅ | ✅ | 스크립트/URL | ❌ | 롱폼→숏폼 |
| **Veed.io** | 제한 | ✅ | UI | ❌ | 자막·편집 SaaS |

### Kaloclip vs Nextify

| | Kaloclip | Nextify |
|---|----------|---------|
| 포지션 | 이커머스 숏폼 올인원 | 퍼포먼스 마케터 광고 스튜디오 |
| 강점 | 경쟁사 벤치마킹, 틱톡샵 | 1000+ 아바타, 15000+ 템플릿 |
| API | 틱톡 공식 API 연동 | REST API 명시 |
| 합격닷컴 | 서비스 URL → 훅 자동 | `hapgyuk.com/start` → UGC 광고 |

---

## 4. 에이전트 네이티브 API — Cursor/Claude가 직접 호출

| 툴 | OpenAPI | Webhook | 엔진 | 가격 | 상태 |
|----|---------|---------|------|------|------|
| **JSON2Video MCP** | ✅ | ✅ | 자체 합성 | $49.95/월 | **프로덕션** |
| **UGC Copilot** | ✅ 3.1 | ✅ HMAC | Sora2, Veo3.1, Kling3, Seedance2 | $0.07/크레딧~ | 라이브 |
| **ReelsBuilder** | ✅ v1 | ✅ | Sora2, Kling, Wan, Seedance | 크레딧제 | Q2-Q3 2026 일부 |
| **Nouvel** | ✅ | ✅ | 자체 UGC | 문의 | 라이브 |
| **US Video API** | ✅ | ✅ | Seedance 2.0 | ~$1.25/클립 | 라이브 |
| **InVideo AI** | ✅ `api.invideo.io` | 폴링 | 자체 | Business+ | 라이브 |

### UGC Copilot 워크플로 (에이전트용)

```
brief → persona → script → scene_image → video_render → overlay → MP4 URL
```

- 26 REST 엔드포인트, Idempotency-Key, TypeScript/Python SDK
- 엔진 선택: testimonial→Sora2, I2V→Kling3, 저비용→Seedance2

### ReelsBuilder Agent Generate

```http
POST /api/v1/generate-and-post
{
  "prompt": "요즘 취준생 사이에서 난리난 AI 자소서 툴",
  "aspect_ratio": "9:16",
  "duration_target_sec": 15,
  "content_style": "ugc_ad",
  "asset_urls": ["https://.../pmax_portrait.png"]
}
```

모드: Magic Video, UGC Ad, Text-to-Video, Image-to-Video, AI Story 등 10+

### US Video API

```bash
POST https://usvideoapi.com/v1/videos
{
  "image_url": "https://.../pmax_square.png",
  "prompt": "Subtle product showcase, mobile UI",
  "aspect_ratio": "9:16",
  "duration": 5
}
```

---

## 5. AI 영상 생성 — 텍스트/이미지 → 클립

**주의:** 통영상 T2V는 **AI 슬롭** → 이전 실패(qT7v1aNCyTg) 반복.  
**Image→Video**로 컨펌 이미지에 **살짝 움직임**만 줄 때만 사용.

| 툴 | API | I2V | 9:16 | 5초 대략 | 비고 |
|----|-----|-----|------|----------|------|
| **Kling 3** | ✅ 직접/래퍼 | ✅ | ✅ | ~$0.12 | 가성비 |
| **Runway Gen-4** | ✅ | ✅ | ✅ | ~$0.50+ | 퀄리티 |
| **Google Veo 3.1** | ✅ Vertex/Gemini | 일부 | 주로 16:9 | 저렴 | 8초, 네이티브 오디오 |
| **Luma Dream Machine** | ✅ | ✅ | ✅ | 중간 | Ray2 |
| **Pika 2** | ✅ | ✅ | ✅ | 중간 | - |
| **Stable Video** | ✅ | ✅ | ✅ | 저렴 | 오픈소스 계열 |
| **Hailuo/MiniMax** | ✅ | ✅ | ✅ | 저렴 | 중국계 |
| **Seedance 2.0** | ✅ (US Video/UGC Copilot) | ✅ | ✅ | 저렴 | ByteDance |
| **Sora 2** | ✅ (OpenAI/래퍼) | ✅ | ✅ | 비쌈 | UGC Copilot 경유 |
| **Pixverse** | ✅ | ✅ | ✅ | 저렴 | ReelsBuilder 연동 |

**래퍼/통합 API:** UGC Copilot, ReelsBuilder, US Video API → 위 엔진을 하나의 키로

---

## 6. 코드 퍼스트 / 오픈소스 — 최대 제어

| 툴 | 스택 | API/MCP | TTS | 자막 | 적합 |
|----|------|---------|-----|------|------|
| **Remotion** | React→MP4 | ✅ Lambda | 직접 | 직접 | 데이터 기반 모션, $100/월 최소(Automators) |
| **OpenMontage** | Python+Remotion | ✅ 에이전트 | Piper(무료) | WhisperX | **$0 API** 파이프라인, 셋업 필요 |
| **MoviePy** | Python | CLI/코드 | 별도 | 별도 | 클립 합성·트림 |
| **FFmpeg** | CLI | Shell | ❌ | burn-in | 포스트프로세싱 (슬라이드쇼 ❌) |
| **montage-ai** | LangGraph+FFmpeg | ✅ MCP | Google TTS | ✅ | 멀티에이전트 실험 |
| **SadTalker** | Python | 로컬 | ❌ | ❌ | 사진+오디오→립싱크 (로컬 GPU) |
| **Wav2Lip** | Python | 로컬 | ❌ | ❌ | 립싱크 오픈소스 |

### Remotion

- https://www.remotion.dev/
- React 컴포넌트 = 영상 프레임
- Lambda/서버리스 대량 렌더
- Automators 플랜: $100/월 최소, $0.01/렌더

### OpenMontage (무료 스택)

```
brief → script → Piper TTS → Pexels B-roll → Remotion 합성 → FFmpeg 인코딩
```

- API 키 $0 가능 (Piper, Archive.org, 무료 스톡)
- 에이전트 비용만 $1~5/영상

---

## 7. SaaS 편집기 — CapCut 대체 (수동, API 제한)

CapCut처럼 **UI에서 편집**하지만, **에이전트 자동화는 어려움**.

| 툴 | 한국어 | 자동자막 | 9:16 | API | 자동화 가능? |
|----|--------|----------|------|-----|--------------|
| **CapCut** | ✅ | ✅ | ✅ | ❌ **없음** | ❌ |
| **Canva** | ✅ | ✅ | ✅ | ❌ (앱 SDK만) | ❌ |
| **Descript** | ✅ | ✅ | ✅ | 제한 | ❌ |
| **Kapwing** | ✅ | ✅ | ✅ | ❌ (플러그인만) | ❌ |
| **InVideo AI** | ✅ | ✅ | ✅ | ✅ Business+ | ⭐⭐⭐ |
| **Veed** | ✅ | ✅ | ✅ | 제한 | ⭐ |
| **Clipchamp** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Adobe Express** | ✅ | ✅ | ✅ | Firefly API 별도 | ⭐ |
| **FlexClip** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Filmora** | ✅ | ✅ | ✅ | ❌ | ❌ |

**InVideo AI**만 이 카테고리에서 `api.invideo.io`로 스크립트→9:16 MP4 자동 생성 가능 (Business 플랜+).

---

## 8. 음성(TTS) / 자막 API — 영상 파이프라인 부품

편집 API에 TTS가 없을 때 조합.

| 툴 | API | 한국어 | 가격 | 용도 |
|----|-----|--------|------|------|
| **ElevenLabs** | ✅ | ✅ | $5+/월 | 최고 품질 VO |
| **Google Cloud TTS** | ✅ | ✅ Neural2 | 사용량 | 안정적, 저렴 |
| **OpenAI TTS** | ✅ | ✅ | 사용량 | 간단 통합 |
| **Azure Speech** | ✅ | ✅ | 사용량 | 엔터프라이즈 |
| **PlayHT** | ✅ | ✅ | $31+/월 | UGC 나레이션 |
| **Typecast** | ✅ | ✅ **한국 특화** | 문의 | 한국어 감정 VO |

자막: **Whisper/WhisperX** (로컬), **AssemblyAI**, **Deepgram** (API)

---

## 합격닷컴 최적 스택 (4안)

### A안 — 에이전트가 끝까지 (API 키 1개) ⭐ 추천

```
JSON2Video MCP + 컨펌 이미지 2장 + (선택) 화면녹화 15초
```

1. JSON2Video API 키 → Cursor MCP
2. V1/V2 대본 → 이미지 인서트 + 한국어 VO + 자막 + 트랜지션
3. YouTube 업로드 → `scripts/add_youtube_asset.py`

### B안 — AI 인플루언서 훅 (품질 우선)

```
D-ID (pmax_portrait → 3초 훅) + JSON2Video (본편 12초)
```

- D-ID: "요즘 취준생 사이에서..."
- JSON2Video: Before/After 이미지 + CTA

### C안 — 손 안 대고 SaaS

```
HeyGen Ad Maker / Nextify / Kaloclip
```

- URL `hapgyuk.com/start` + 스크립트
- 9:16 export → YouTube → PMax

### D안 — 에이전트 + AI 엔진 라우팅

```
UGC Copilot API 또는 ReelsBuilder API
```

- brief 1개 → 10변형 A/B
- webhook으로 완료 수신

---

## 가격 비교 (15초 9:16 1개 대략)

| 방법 | 비용 | 퀄리티 | 자동화 |
|------|------|--------|--------|
| FFmpeg 슬라이드쇼 (v1 시도) | $0 | ❌ | ✅ |
| JSON2Video | ~$0.15 | ⭐⭐⭐ | ✅ MCP |
| D-ID 3초 + JSON2Video 12초 | ~$0.25 | ⭐⭐⭐⭐ | ✅ |
| HeyGen API 15초 | ~$0.25 | ⭐⭐⭐⭐⭐ | ✅ |
| Nextify 1크레딧 | 플랜별 | ⭐⭐⭐⭐ | ✅ |
| UGC Copilot (Seedance) | ~$1~3 | ⭐⭐⭐ | ✅ |
| Kaloclip | 플랜별 | ⭐⭐⭐⭐ UGC | 플랫폼 |
| Kling I2V 5초만 | ~$0.12 | ⭐⭐ | ✅ |
| OpenMontage (무료 스택) | ~$0 + 에이전트 | ⭐⭐⭐ | ⭐⭐ 셋업 |
| CapCut 수동 | $0 | ⭐⭐⭐⭐ | ❌ |

---

## API / MCP 연동 가능 여부 — 전체 매트릭스

| 툴 | REST API | MCP | Webhook | 9:16 | 한국어 |
|----|----------|-----|---------|------|--------|
| JSON2Video | ✅ | ✅ | ✅ | ✅ | ✅ |
| Creatomate | ✅ | ❌ | ✅ | ✅ | TTS |
| Shotstack | ✅ | ❌ | ✅ | ✅ | 별도 |
| Placid | ✅ | ❌ | ✅ | ✅ | 별도 |
| Plainly | ✅ | ❌ | ✅ | ✅ | 별도 |
| Moovly | ✅ | ❌ | ✅ | ✅ | ✅ |
| D-ID | ✅ | ❌ | ✅ | ✅ | ✅ |
| HeyGen | ✅ | ❌ | ✅ | ✅ | ✅ |
| Nextify | ✅ | ❌ | ✅ | ✅ | ✅ |
| Creatify | ✅ | ❌ | ✅ | ✅ | ✅ |
| Nouvel | ✅ | ❌ | ✅ | ✅ | 자동 |
| Kaloclip | 플랫폼 | ❌ | ❌ | ✅ | ✅ |
| UGC Copilot | ✅ | OpenAPI | ✅ | ✅ | ✅ |
| ReelsBuilder | ✅ | 문서화 | ✅ | ✅ | ✅ |
| US Video API | ✅ | ❌ | ✅ | ✅ | 프롬프트 |
| InVideo AI | ✅ | ❌ | 폴링 | ✅ | ✅ |
| Remotion | ✅ | ❌ | ❌ | ✅ | 직접 |
| Kling/Runway/Veo | ✅ | ❌ | ✅ | ✅ | 프롬프트 |
| CapCut | ❌ | ❌ | ❌ | ✅ | ✅ |
| Canva | ❌ | ❌ | ❌ | ✅ | ✅ |
| Kapwing | ❌ | ❌ | ❌ | ✅ | ✅ |

---

## 하지 말 것

- ❌ FFmpeg 이미지+글자 슬라이드 (v1 실패 — AI 슬롭)
- ❌ Headless 브라우저 녹화 (빈 화면)
- ❌ CapCut 계정 로그인 자동화 (API 없음, ToS 위험)
- ❌ Kling/Sora로 **통영상** 생성 (전환 0, AI 느낌)
- ❌ Canva/Kapwing API 있다고 가정 (실제로는 UI/SDK만)

---

## 지금 당장 필요한 것

| 우선순위 | 키/자료 | 용도 |
|----------|---------|------|
| **1** | JSON2Video API key | MCP → 에이전트 렌더 |
| 2 | D-ID API key | portrait 훅 3초 |
| 3 | HeyGen API credits (선택) | 최고 퀄 대안 |
| 4 | 화면녹화 15초 (폰) | `hapgyuk.com/start` 실제 UI |
| 5 | Nextify/Kaloclip 계정 (선택) | UGC 스타일 원스톱 |

---

## 다음 액션

1. **JSON2Video** 가입 → API 키 → Cursor MCP 등록
2. 키 주시면 V1/V2 **제대로 된** 9:16 MP4 (이미지 인서트+한국어 VO+자막+컷)
3. D-ID 키 있으면 `pmax_portrait` **인플루언서 훅 3초** 추가
4. YouTube `video_id` → `scripts/add_youtube_asset.py --video-id XXX` → PMax

---

## 참고 링크

| 툴 | URL |
|----|-----|
| JSON2Video MCP | https://json2video.com/docs/v2/help-for-ai-agents/mcp-server |
| D-ID API | https://docs.d-id.com/ |
| HeyGen API | https://docs.heygen.com/ |
| UGC Copilot API | https://ugccopilot.ai/api/ |
| ReelsBuilder API | https://reelsbuilder.ai/docs/api |
| Creatomate | https://creatomate.com/ |
| Shotstack | https://shotstack.io/ |
| Nextify KO | https://www.nextify.ai/ko |
| Kaloclip | https://www.kaloclip.com/ (한국어) |
| Remotion | https://www.remotion.dev/ |
| OpenMontage | https://github.com/ (에이전트 파이프라인) |
