# 영상 제작 — 현황 & CapCut 대안

## v1_ai_influencer_hook_9x16.mp4 는 폐기함

이미지에 글자 덧씌운 **슬라이드쇼**였음. 릴스/광고 수준이 아님.

---

## CapCut 말고 — 전체 대안 조사

**→ [`../video_tools_research.md`](../video_tools_research.md)** (50+ 툴, API/MCP 매트릭스)

| 추천 | 툴 | 이유 |
|------|-----|------|
| 1순위 | **JSON2Video** + MCP | Cursor 에이전트가 직접 렌더 |
| 훅 3초 | **D-ID** | `pmax_portrait` 사진→말하는 영상 |
| 원스톱 | **Nextify / Kaloclip / HeyGen** | URL→UGC 광고 |
| 에이전트 | **UGC Copilot / ReelsBuilder** | brief→10변형 A/B |

CapCut은 **공개 API 없음** — 계정 로그인 자동화 불가.

---

## 여기서 자동으로 못 하는 것

| 항목 | 이유 |
|------|------|
| CapCut 계정 연동 | API 없음 |
| FFmpeg 슬라이드쇼 | v1 품질 실패 |
| 서버 headless 녹화 | hapgyuk.com/start 빈 화면 |

---

## API 키 있으면 에이전트가 할 수 있는 것

1. JSON2Video MCP → V1/V2 대본으로 9:16 MP4 (이미지 인서트+VO+자막)
2. D-ID → portrait 3초 인플루언서 훅
3. YouTube 업로드 → `scripts/add_youtube_asset.py`

---

## 수동 제작 (폰 녹화 + 편집기)

CapCut / Canva / Descript / InVideo 등 UI 편집기 사용.

### 1) 훅 3초 — 셀카 or D-ID
> "요즘 취준생 사이에서 진짜 난리난 거 알아? AI 자소서 첨삭인데."

### 2) 본편 10초 — 화면 녹화
- `hapgyuk.com/start` → 데모 ATS 59점 → "내 자소서 진단하기"

### 3) 편집 (CapCut 등)
- 9:16, 훅+녹화 이어붙이기, 자막, 트랜지션, 엔드카드

### 4) 이미지는 인서트만
컨펌 PNG 2장은 **전체 화면 X** — 1~2초 PIP 또는 엔드카드만.

| 파일 | 용도 |
|------|------|
| `pmax_portrait_960x1200.png` | 엔드카드 or D-ID 훅 소스 |
| `pmax_square_1200x1200.png` | Before/After 1.5초 인서트 |

---

## YouTube → PMax

```bash
python3 scripts/add_youtube_asset.py --video-id YOUR_ID
```
