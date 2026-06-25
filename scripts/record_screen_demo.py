#!/usr/bin/env python3
"""Record real hapgyuk.com/start UI for ad video (not image slideshow)."""
import asyncio
import subprocess
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "creatives" / "videos"
RAW = OUT / "screen_raw.webm"
FINAL = OUT / "v1_screen_demo_9x16.mp4"
URL = "https://hapgyuk.com/start"
VIEWPORT = {"width": 390, "height": 844}  # iPhone-ish


async def record():
    OUT.mkdir(parents=True, exist_ok=True)
    if RAW.exists():
        RAW.unlink()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport=VIEWPORT,
            device_scale_factor=3,
            record_video_dir=str(OUT),
            record_video_size={"width": VIEWPORT["width"], "height": VIEWPORT["height"]},
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            ),
        )
        page = await context.new_page()
        await page.goto(URL, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(2000)
        # Scroll through demo content
        for _ in range(4):
            await page.mouse.wheel(0, 400)
            await page.wait_for_timeout(800)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(1000)
        await context.close()
        await browser.close()

    # Playwright saves with random name in OUT
    webms = list(OUT.glob("*.webm"))
    if not webms:
        raise SystemExit("No recording produced")
    webms[0].rename(RAW)


def postprocess():
    """Pad to 9:16 1080x1920, trim to 12s."""
    subprocess.run([
        "ffmpeg", "-y", "-i", str(RAW),
        "-t", "12",
        "-vf", (
            "scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x0f172a,"
            "fps=30"
        ),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-an",
        str(FINAL),
    ], check=True)


async def main():
    await record()
    postprocess()
    print(f"OK: {FINAL}")


if __name__ == "__main__":
    asyncio.run(main())
