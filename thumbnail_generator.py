#!/usr/bin/env python3
"""
AI Reel Thumbnail Generator (Vertical 9:16)
===========================================
Generates ultra-high-definition vertical thumbnails for Facebook Reels using:
1. Flux AI / Flow AI (Pollinations Engine) - Fast, Free, 8k HD
2. Fal.ai / Imagen / OmniRoute (if configured via THUMBNAIL_API_KEY)
"""

import os
import sys
import time
import urllib.parse
import requests

def generate_vertical_thumbnail(prompt, output_filename="thumbnail.jpg", output_dir="logs"):
    """
    Generates a 1080x1920 (9:16 aspect ratio) cover thumbnail based on prompt.
    """
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, output_filename)

    enhanced_prompt = (
        f"{prompt}, vertical 9:16 aspect ratio, cinematic lighting, movie poster aesthetic, "
        "ultra-detailed, 8k resolution, highly engaging YouTube/Facebook Reel thumbnail, photorealistic"
    )

    encoded = urllib.parse.quote(enhanced_prompt)

    # 1. Primary Engine: Flux AI / Pollinations HD
    flux_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&model=flux&nologo=true&seed={int(time.time())}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }

    print(f"🎨 Generating 9:16 Thumbnail with Flux AI...")
    try:
        resp = requests.get(flux_url, headers=headers, timeout=60)
        if resp.status_code == 200 and len(resp.content) > 2000:
            with open(out_path, "wb") as f:
                f.write(resp.content)
            print(f"✅ Thumbnail successfully generated: {out_path} ({len(resp.content)/1024:.1f} KB)")
            return out_path
        else:
            print(f"⚠️ Primary engine returned status {resp.status_code}")
    except Exception as ex:
        print(f"⚠️ Primary thumbnail engine note: {ex}")

    # 2. Fallback Engine: Turbo / Stable Diffusion
    try:
        turbo_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&model=turbo&nologo=true"
        resp2 = requests.get(turbo_url, headers=headers, timeout=60)
        if resp2.status_code == 200 and len(resp2.content) > 2000:
            with open(out_path, "wb") as f:
                f.write(resp2.content)
            print(f"✅ Fallback thumbnail generated: {out_path}")
            return out_path
    except Exception as ex2:
        print(f"❌ All thumbnail engines failed: {ex2}")

    return None

if __name__ == "__main__":
    test_prompt = "Study in USA and Canada from Nepal, happy students with graduation caps, modern glowing futuristic background"
    res = generate_vertical_thumbnail(test_prompt, "test_thumbnail.jpg", "logs")
    print("Result path:", res)
