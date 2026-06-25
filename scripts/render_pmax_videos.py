#!/usr/bin/env python3
"""Render PMax vertical videos from approved creative images + scripts."""
import os
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CREATIVES = ROOT / "creatives"
OUT = CREATIVES / "videos"
PORTRAIT = CREATIVES / "pmax_portrait_960x1200.png"
SQUARE = CREATIVES / "pmax_square_1200x1200.png"
FONT = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
W, H = 1080, 1920
FPS = 30


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def fit_cover(img: Image.Image, w: int, h: int) -> Image.Image:
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    return img.crop((left, top, left + w, top + h))


def render_frame(bg_path: Path | None, lines: list[tuple[str, str, int]], bg_color="#0f172a") -> Image.Image:
    """lines: [(text, color, size), ...]"""
    if bg_path and bg_path.exists():
        base = fit_cover(Image.open(bg_path).convert("RGB"), W, H)
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 120))
        base = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    else:
        base = Image.new("RGB", (W, H), bg_color)

    draw = ImageDraw.Draw(base)
    y = 180
    for text, color, size in lines:
        font = ImageFont.truetype(FONT, size)
        for line in textwrap.wrap(text, width=16):
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) // 2, y), line, fill=color, font=font)
            y += size + 12
    return base


def frame_to_clip(frame: Image.Image, duration: float, out: Path, zoom=1.0):
    tmp = out.with_suffix(".png")
    frame.save(tmp)
    frames = max(int(duration * FPS), 1)
    zf = 1 + (0.08 if zoom else 0)
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},"
        f"zoompan=z='min(zoom+0.001,{zf})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={W}x{H}:fps={FPS}"
    )
    run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(tmp),
        "-vf", vf,
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        str(out),
    ])
    tmp.unlink(missing_ok=True)


def concat_clips(clips: list[Path], out: Path):
    lst = out.with_suffix(".txt")
    lst.write_text("\n".join(f"file '{c}'" for c in clips))
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
        "-c", "copy", str(out),
    ])
    lst.unlink(missing_ok=True)


def build_v1(tmp_dir: Path) -> Path:
  """요즘 AI 자소서 툴 — AI 인플루언서 훅"""
  scenes = [
    (None, [("요즘 취준생 사이에서", "#FFFFFF", 72), ("난리난 AI 툴 🤯", "#FFE135", 88)], 1.5),
    (PORTRAIT, [("복잡한 자소서", "#FFFFFF", 64), ("AI가 깔끔하게!", "#93C5FD", 72)], 2.0),
    (SQUARE, [("첨삭 전 → 첨삭 후", "#FFFFFF", 68), ("95점 AI 피드백", "#4ADE80", 72)], 3.0),
    (PORTRAIT, [("AI 자소서 첨삭 3분", "#FFFFFF", 76), ("₩5,900", "#FFE135", 96)], 3.0),
    (SQUARE, [("지금 무료 진단", "#FFFFFF", 80), ("hapgyuk.com/start", "#60A5FA", 56)], 2.5),
    (PORTRAIT, [("합격닷컴", "#FFFFFF", 88), ("3분 완성 · 합격률 UP", "#CBD5E1", 48)], 3.0),
  ]
  clips = []
  for i, (bg, lines, dur) in enumerate(scenes):
    frame = render_frame(bg, lines)
    clip = tmp_dir / f"v1_{i}.mp4"
    frame_to_clip(frame, dur, clip, zoom=bool(bg))
    clips.append(clip)
  out = OUT / "v1_ai_influencer_hook_9x16.mp4"
  concat_clips(clips, out)
  return out


def build_v2(tmp_dir: Path) -> Path:
  """자소서 첨삭 10만원 아끼는 법 — 레퍼런스 훅"""
  scenes = [
    (None, [("자소서 첨삭", "#FFFFFF", 80), ("10만원 아끼는 법 🤯", "#FFE135", 88)], 2.0),
    (SQUARE, [("요즘 AI 자소서 툴", "#FFFFFF", 68), ("합격닷컴 AI 첨삭", "#60A5FA", 72)], 2.5),
    (SQUARE, [("구체성 부족 → 30% 성과", "#FFFFFF", 56), ("95점 피드백", "#4ADE80", 72)], 3.5),
    (PORTRAIT, [("붙여넣기만 하면", "#FFFFFF", 68), ("3분 만에 첨삭", "#FFE135", 80)], 3.0),
    (PORTRAIT, [("진단 무료", "#4ADE80", 80), ("첨삭 ₩5,900", "#FFFFFF", 72)], 2.5),
    (SQUARE, [("지금 무료 진단 >", "#FFFFFF", 76), ("hapgyuk.com/start", "#60A5FA", 52)], 2.5),
  ]
  clips = []
  for i, (bg, lines, dur) in enumerate(scenes):
    frame = render_frame(bg, lines)
    clip = tmp_dir / f"v2_{i}.mp4"
    frame_to_clip(frame, dur, clip, zoom=bool(bg))
    clips.append(clip)
  out = OUT / "v2_save_money_hook_9x16.mp4"
  concat_clips(clips, out)
  return out


def build_v4(tmp_dir: Path) -> Path:
  """ATS 59 → 80점 숫자 훅"""
  scenes = [
    (None, [("59점", "#EF4444", 120), ("서류 탈락 위험", "#FFFFFF", 64)], 2.0),
    (SQUARE, [("첨삭 전", "#FCA5A5", 72), ("↓ AI 3분", "#FFFFFF", 64)], 2.0),
    (SQUARE, [("첨삭 후 95점", "#4ADE80", 88), ("합격 구조", "#FFFFFF", 64)], 3.0),
    (PORTRAIT, [("ATS 진단 + 첨삭", "#FFFFFF", 68), ("무제한 첨삭", "#93C5FD", 56)], 3.0),
    (PORTRAIT, [("지금 무료 진단", "#FFE135", 80), ("hapgyuk.com/start", "#60A5FA", 52)], 2.5),
  ]
  clips = []
  for i, (bg, lines, dur) in enumerate(scenes):
    frame = render_frame(bg, lines)
    clip = tmp_dir / f"v4_{i}.mp4"
    frame_to_clip(frame, dur, clip, zoom=bool(bg))
    clips.append(clip)
  out = OUT / "v4_ats_score_9x16.mp4"
  concat_clips(clips, out)
  return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "_tmp"
    tmp.mkdir(exist_ok=True)
    results = {}
    for name, fn in [("v1", build_v1), ("v2", build_v2), ("v4", build_v4)]:
        print(f"Rendering {name}...")
        path = fn(tmp)
        size_mb = path.stat().st_size / 1_048_576
        print(f"  -> {path} ({size_mb:.1f} MB)")
        results[name] = str(path)
    # cleanup tmp clips
    for f in tmp.glob("*.mp4"):
        f.unlink()
    tmp.rmdir()
    print("\nDone:", results)


if __name__ == "__main__":
    main()
