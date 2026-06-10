# 합격닷컴 PMax 영상 v2 (15초) — 제작 스크립트

기존 영상 `qT7v1aNCyTg` (10초, 조회 396) 대비 개선안.
이 환경에서는 MP4 렌더/YouTube 업로드 자동화 불가 → 스크립트 제공.

## Storyboard (9:16 세로)

| 초 | 화면 | 자막/VO |
|----|------|---------|
| 0-2 | 자소서에 빨간 밑줄 촌스러운 문장 | "이 문장, HR이 3초 만에 스킵합니다" |
| 2-5 | hapgyuk.com/start 에 붙여넣기 | "자소서 붙여넣고" |
| 5-8 | AI 첨삭 로딩 → 초록 체크 | "3분이면 STAR 구조로 재작성" |
| 8-11 | 합격 점수 UI + 5,900원 | "서류 합격 진단 ₩5,900" |
| 11-15 | CTA 버튼 클릭 | "지금 무료 진단 → hapgyuk.com/start" |

## CapCut / Canva 프롬프트

```
9:16 vertical SaaS ad, Korean job seeker pastes cover letter into AI editor,
red rejected lines turn green structured STAR bullets, modern blue-white UI,
Korean subtitles, 15 seconds, upbeat corporate BGM, CTA: 무료 진단
```

## YouTube 업로드 후

```bash
# 업로드된 video_id로 PMax asset 추가 (수동 또는 API)
python3 scripts/add_youtube_asset.py --video-id YOUR_VIDEO_ID
```
