# PMax 영상 제작 — CapCut / YouTube 가이드

## CapCut 직접 연결에 대해

**CapCut은 공개 API가 없어서** 에이전트가 계정 로그인해서 자동 편집하는 건 **기술적으로 불가**합니다.  
(계정 비밀번호를 채팅으로 주셔도 보안상 권장하지 않음)

**대신 여기서 한 것:**
- 컨펌된 이미지 2장 기반으로 **9:16 MP4 3개** 렌더 완료 (`creatives/videos/`)
- 기획안의 V1/V2/V4 대본 + 이미지 카피 반영

---

## 렌더된 파일

| 파일 | 컨셉 | 길이 |
|------|------|------|
| `v1_ai_influencer_hook_9x16.mp4` | 요즘 AI 자소서 툴 훅 | ~15초 |
| `v2_save_money_hook_9x16.mp4` | 10만원 아끼는 법 | ~16초 |
| `v4_ats_score_9x16.mp4` | 59점→95점 | ~12.5초 |

### 이미지에서 가져온 카피
- **세로:** Before/After, AI 3분, ₩5,900, 합격률 UP, 무제한 첨삭
- **정사각:** 첨삭 전/후, 95점, 지금 무료 진단, 구체성→30% 성과

---

## CapCut에서 마무리 (선택)

1. CapCut 데스크톱 → **가져오기** → 위 MP4
2. **트렌드 BGM** 추가 (업비트)
3. **자동 자막** 재생성 후 키워드 노란색 강조
4. 첫 1.5초에 **줌 인** 효과 (이미 약간 들어감)
5. export 1080×1920

---

## YouTube → PMax (권장)

1. YouTube에 **비공개** 업로드
2. video_id 확인
3. Google Ads → PMax → 자산 → YouTube 동영상 추가  
   또는 (토큰 복구 후):
```bash
python3 scripts/add_youtube_asset.py --video-id YOUR_ID
```

---

## 더 많은 이미지 추가

컨펌하신 이미지가 2장 말고 더 있으면:
- `creatives/` 폴더에 PNG 넣기
- `python3 scripts/render_pmax_videos.py` 재실행

---

## 실제 UI 녹화 버전 (권장 업그레이드)

지금 버전은 **이미지 슬라이드 + 자막**입니다.  
전환율 최대화하려면 `hapgyuk.com/start` **화면 녹화 30초**를 주시면  
V1/V2에 합쳐서 v1.1 리렌더 가능합니다.

재렌더:
```bash
python3 scripts/render_pmax_videos.py
```
