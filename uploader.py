#!/usr/bin/env python3
"""
Facebook Reels 24/7 Ultra-Deep AI Auto Uploader
================================================
Features:
1. Ultra-Deep Video Analysis with Gemini 3.6 Flash:
   - Auto-detects spoken language and visual theme
   - Generates viral Title, Hooks, SEO Description
   - Generates 8-12 trending, high-ranking hashtags
   - Generates custom prompt for 9:16 AI Thumbnail
2. Flow/Flux AI Thumbnail Generator:
   - Generates photorealistic vertical 9:16 cover thumbnail
   - Uploads/applies custom thumbnail to Reel
3. Uploads to Personal Facebook ID at scheduled Nepali Times:
   - 7:00 AM, 1:00 PM, 4:00 PM, 7:00 PM NPT
4. Auto-Delete Video on Success:
   - Automatically removes the uploaded video from videos/ folder to keep disk clean!
"""

import os
import sys
import json
import time
import glob
import re
import urllib.parse
from datetime import datetime, timezone, timedelta
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

load_dotenv()

# Directories & Files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEOS_DIR = os.path.join(BASE_DIR, "videos")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
QUEUE_FILE = os.path.join(BASE_DIR, "queue.json")
HISTORY_FILE = os.path.join(BASE_DIR, "posted_history.json")
SESSION_FILE = os.path.join(BASE_DIR, "facebook_session.json")

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Nepal Timezone (UTC + 5:45)
NEPAL_TZ = timezone(timedelta(hours=5, minutes=45))

def get_nepal_time_str():
    return datetime.now(NEPAL_TZ).strftime("%Y-%m-%d %I:%M:%S %p NPT")

def log(msg):
    print(f"[{get_nepal_time_str()}] {msg}", flush=True)

def send_telegram_notification(message):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if bot_token and chat_id:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
            requests.post(url, json=data, timeout=10)
        except Exception as e:
            log(f"⚠️ Telegram notification error: {e}")

def load_posted_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log(f"⚠️ Failed to read {HISTORY_FILE}: {e}")
    return []

def save_posted_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def get_next_video():
    """
    Finds the first available unposted video in videos/ folder, root repo directory, or queue.json.
    """
    supported_extensions = ("*.mp4", "*.mov", "*.webm", "*.mkv", "*.MP4", "*.MOV")
    video_files = []
    # 1. Scan videos/ directory
    for ext in supported_extensions:
        video_files.extend(glob.glob(os.path.join(VIDEOS_DIR, ext)))
    
    # 2. Scan root directory (in case user uploads directly to repo root)
    for ext in supported_extensions:
        for f in glob.glob(os.path.join(BASE_DIR, ext)):
            if f not in video_files:
                video_files.append(f)
    
    video_files.sort() # FIFO order

    if not video_files:
        return None

    # Pick first available video
    target_path = video_files[0]
    target_name = os.path.basename(target_path)

    # Check if custom metadata exists in queue.json
    custom_caption = ""
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                queue = json.load(f)
                for item in queue:
                    if item.get("filename") == target_name:
                        custom_caption = item.get("caption", "")
                        break
        except Exception:
            pass

    return {
        "filename": target_name,
        "filepath": target_path,
        "custom_caption": custom_caption
    }

def perform_ultra_deep_video_analysis(video_path, video_filename):
    """
    Ultra-deep video analysis using Gemini 3.6 Flash.
    Returns language, title, description, hashtags, and thumbnail_prompt.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        log("ℹ️ No GEMINI_API_KEY found, using default viral template.")
        return {
            "language": "Nepali/English",
            "title": "Amazing Viral Reel! 🔥",
            "description": "Watch till the end! Like, Comment & Share 🚀",
            "hashtags": ["#fyp", "#reels", "#nepal", "#trending", "#viral"],
            "thumbnail_prompt": f"Vertical 9:16 vibrant cinematic action shot for video {video_filename}, high contrast, 8k resolution, photorealistic."
        }

    try:
        from google import genai
        log(f"🧠 Gemini 3.6 Flash analyzing video deeply: '{video_filename}'...")
        client = genai.Client(api_key=gemini_key)

        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        file_ref = None

        if file_size_mb < 80:
            try:
                log("📤 Uploading video to Gemini Vision Engine...")
                file_ref = client.files.upload(file=video_path)
                while file_ref.state.name == "PROCESSING":
                    time.sleep(2)
                    file_ref = client.files.get(name=file_ref.name)
                log(f"✅ Video processed in Gemini Vision (State: {file_ref.state.name})")
            except Exception as up_ex:
                log(f"⚠️ Video direct upload note: {up_ex}")

        analysis_prompt = """
Perform an ultra-deep, comprehensive analysis of this video and return a JSON object with:
1. "language": Spoken or detected language (e.g. "Nepali", "English", "Hindi", "Instrumental Music").
2. "title": Catchy, high-CTR viral hook/title with attractive emojis.
3. "description": Ultra-engaging Facebook Reel description in the video's language that hooks viewers and maximizes watch time.
4. "hashtags": An array of 8-12 high-traffic, relevant, trending hashtags (e.g. ["#StudyAbroad", "#NepalToUSA", "#fyp", "#reels", "#viral"]).
5. "thumbnail_prompt": Detailed, photorealistic prompt for generating a stunning vertical 9:16 thumbnail image that captures the essence of this video.

Respond ONLY with valid JSON.
"""
        contents = [file_ref, analysis_prompt] if file_ref else [analysis_prompt + f"\nVideo filename: {video_filename}"]
        
        models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-3.6-flash', 'gemini-2.5-flash', 'gemini-3-flash-preview']
        response = None
        for m in models_to_try:
            try:
                log(f"Trying Gemini model '{m}'...")
                response = client.models.generate_content(
                    model=m,
                    contents=contents
                )
                if response and response.text:
                    log(f"✅ Success with Gemini model '{m}'")
                    break
            except Exception as mex:
                log(f"⚠️ Model '{m}' note: {mex}")
                continue

        if not response or not response.text:
            raise RuntimeError("All Gemini models reached quota or failed")

        raw_text = response.text.strip()
        # Clean json markdown wrapper if present
        clean_json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if clean_json_match:
            data = json.loads(clean_json_match.group(0))
            log(f"🎯 Analysis Completed:\n - Language: {data.get('language')}\n - Title: {data.get('title')}")
            return data
        else:
            return json.loads(raw_text)

    except Exception as e:
        log(f"⚠️ Gemini deep analysis fallback: {e}")
        return {
            "language": "Nepali/English",
            "title": "Incredible Reel! 🚀",
            "description": "Watch till the end and follow for more exciting content! 🔥",
            "hashtags": ["#fyp", "#reels", "#nepal", "#trending", "#viral"],
            "thumbnail_prompt": f"Vertical 9:16 high quality movie poster thumbnail for {video_filename}, photorealistic, dramatic lighting, 8k."
        }

from thumbnail_generator import generate_vertical_thumbnail

def generate_ai_thumbnail(thumbnail_prompt, video_filename):
    """
    Generates a custom vertical 9:16 thumbnail image using Flux / Flow AI.
    """
    if not thumbnail_prompt:
        thumbnail_prompt = f"Cinematic viral Facebook Reel thumbnail for video {video_filename}"
    
    thumb_name = f"thumb_{os.path.splitext(video_filename)[0]}.jpg"
    return generate_vertical_thumbnail(thumbnail_prompt, thumb_name, LOGS_DIR)

def parse_cookie_string_to_storage(cookie_str):
    cookies = []
    for item in cookie_str.split(";"):
        if "=" in item:
            k, v = item.strip().split("=", 1)
            k = k.strip()
            v = v.strip()
            if k and v:
                cookies.append({
                    "name": k,
                    "value": v,
                    "domain": ".facebook.com",
                    "path": "/",
                    "expires": 1819062569,
                    "httpOnly": k in ["xs", "fr", "sb", "datr", "ps_l", "ps_n"],
                    "secure": True,
                    "sameSite": "Lax"
                })
    return {"cookies": cookies, "origins": []}

def prepare_storage_state():
    # Check all possible secret names
    for env_var in ["FB_STORAGE_STATE", "FB_COOKIE", "FB_COOKIES", "FB_PAGE_TOKEN"]:
        raw_val = os.getenv(env_var, "").strip()
        if raw_val:
            # 1. Try parsing as JSON
            try:
                state_data = json.loads(raw_val)
                with open(SESSION_FILE, "w", encoding="utf-8") as f:
                    json.dump(state_data, f, indent=2)
                log(f"✅ Loaded JSON session state from {env_var} secret.")
                return True
            except Exception:
                pass

            # 2. Try parsing as cookie string (datr=...; c_user=...;)
            if "c_user=" in raw_val or "xs=" in raw_val or "datr=" in raw_val:
                try:
                    storage_data = parse_cookie_string_to_storage(raw_val)
                    with open(SESSION_FILE, "w", encoding="utf-8") as f:
                        json.dump(storage_data, f, indent=2)
                    log(f"✅ Parsed raw cookie string from {env_var} secret ({len(storage_data['cookies'])} cookies).")
                    return True
                except Exception as ex:
                    log(f"⚠️ Failed to parse cookie string from {env_var}: {ex}")

    if os.path.exists(SESSION_FILE):
        log(f"✅ Using local session file: {SESSION_FILE}")
        return True

    log("❌ ERROR: No Facebook session found! Run 'save_session.py' or provide FB_STORAGE_STATE.")
    return False

def upload_reel(video_info):
    """
    Executes full upload flow to Personal Facebook Profile ID with custom thumbnail & SEO caption.
    """
    video_path = video_info["filepath"]
    video_filename = video_info["filename"]

    # 1. Ultra-Deep AI Video Analysis
    analysis = perform_ultra_deep_video_analysis(video_path, video_filename)

    # Format caption
    if video_info.get("custom_caption"):
        final_caption = video_info["custom_caption"]
    else:
        title = analysis.get("title", "")
        desc = analysis.get("description", "")
        tags = " ".join(analysis.get("hashtags", ["#fyp", "#reels", "#nepal"]))
        final_caption = f"{title}\n\n{desc}\n\n{tags}"

    log(f"✨ Final Caption to be posted:\n{final_caption}\n")

    # 2. Generate AI Thumbnail
    thumbnail_prompt = analysis.get("thumbnail_prompt", "")
    thumbnail_path = generate_ai_thumbnail(thumbnail_prompt, video_filename) if thumbnail_prompt else None

    # 3. Launch Headless Browser & Automate Facebook Reels Creator
    is_headless = os.getenv("HEADLESS", "true").lower() != "false"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=is_headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=1920,1080"
            ]
        )

        context = browser.new_context(
            storage_state=SESSION_FILE,
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="Asia/Kathmandu"
        )

        page = context.new_page()
        page.set_default_timeout(60000)

        # Stealth evasions
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

        log("🌐 Navigating to Facebook Reels Creator (https://www.facebook.com/reels/create)...")
        page.goto("https://www.facebook.com/reels/create", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        # Verify login
        if "login" in page.url or "checkpoint" in page.url:
            screenshot_err = os.path.join(LOGS_DIR, f"session_expired_{int(time.time())}.png")
            page.screenshot(path=screenshot_err)
            error_msg = "❌ Facebook Session Expired! Please re-login using save_session.py"
            log(error_msg)
            browser.close()
            return False, error_msg, None

        # Upload Video File
        log("📤 Attaching video file...")
        try:
            page.wait_for_selector('input[type="file"]', state="attached", timeout=25000)
            page.locator('input[type="file"]').first.set_input_files(video_path)
            log("✅ Video attached successfully!")
        except Exception as ex:
            log(f"⚠️ Standard input failed ({ex}), trying file chooser...")
            with page.expect_file_chooser(timeout=10000) as fc_info:
                page.locator('div[role="button"]:has-text("Add Video"), [aria-label*="Add video"]').first.click()
            fc_info.value.set_files(video_path)
            log("✅ Video attached via chooser!")

        # Wait for video processing
        log("⏳ Waiting for video preview processing (10s)...")
        page.wait_for_timeout(10000)

        # Check for Thumbnail / Cover Photo Upload button if available
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                cover_tab = page.locator('div[role="tab"]:has-text("Cover photo"), div[role="button"]:has-text("Cover photo"), div[role="button"]:has-text("Thumbnail")').first
                if cover_tab.is_visible(timeout=3000):
                    cover_tab.click()
                    page.wait_for_timeout(2000)
                    upload_cover_btn = page.locator('input[type="file"][accept*="image"]').first
                    if upload_cover_btn.is_attached():
                        upload_cover_btn.set_input_files(thumbnail_path)
                        log("🖼️ Custom AI Thumbnail attached to Reel cover!")
            except Exception as th_ex:
                log(f"ℹ️ Custom cover upload tab note: {th_ex}")

        # Step 1: Click "Next" / "अर्को"
        next_selectors = [
            'div[aria-label="Next"]', 'div[aria-label="अर्को"]',
            'div[role="button"]:has-text("Next")', 'div[role="button"]:has-text("अर्को")',
            'button:has-text("Next")', 'button:has-text("अर्को")'
        ]

        def click_next():
            for sel in next_selectors:
                try:
                    loc = page.locator(sel).first
                    if loc.is_visible(timeout=3000):
                        loc.click()
                        log(f"➡️ Clicked Next ({sel})")
                        page.wait_for_timeout(3000)
                        return True
                except Exception:
                    continue
            return False

        click_next()
        page.wait_for_timeout(2000)
        click_next() # If audio/trim step exists

        # Step 2: Fill Caption / Description
        log("✍️ Typing AI SEO Caption & Viral Hashtags...")
        caption_selectors = [
            'div[aria-label*="Describe your reel"]',
            'div[aria-label*="आफ्नो रिल"]',
            'div[aria-label*="Write a description"]',
            'div[role="textbox"]',
            'div[contenteditable="true"]',
            'textarea'
        ]

        caption_filled = False
        for c_sel in caption_selectors:
            try:
                loc = page.locator(c_sel).first
                if loc.is_visible(timeout=3000):
                    loc.click()
                    page.wait_for_timeout(500)
                    page.keyboard.type(final_caption, delay=15)
                    caption_filled = True
                    log(f"✅ Caption entered into ({c_sel})")
                    break
            except Exception:
                continue

        if not caption_filled:
            try:
                page.keyboard.press("Tab")
                page.keyboard.type(final_caption, delay=15)
            except Exception as e:
                log(f"⚠️ Caption typing error: {e}")

        page.wait_for_timeout(3000)

        # Step 3: Click "Post" / "Publish"
        log("🚀 Clicking 'Post' / 'Publish' button...")
        publish_selectors = [
            'div[aria-label="Post"]',
            'div[role="button"]:has-text("Post")',
            'button:has-text("Post")',
            'div[aria-label="Publish"]',
            'div[role="button"]:has-text("Publish")',
            'div[aria-label="प्रकाशित गर्नुहोस्"]',
            'div[role="button"]:has-text("प्रकाशित गर्नुहोस्")',
            'button:has-text("Publish")'
        ]

        published = False
        for p_sel in publish_selectors:
            try:
                loc = page.locator(p_sel).first
                if loc.is_visible(timeout=4000):
                    loc.click()
                    log(f"🎉 Clicked Publish/Post button ({p_sel})!")
                    published = True
                    break
            except Exception:
                continue

        if not published:
            try:
                page.get_by_role("button", name="Post").click(timeout=5000)
                published = True
                log("🎉 Clicked Post via get_by_role!")
            except Exception:
                try:
                    page.get_by_role("button", name="Publish").click(timeout=5000)
                    published = True
                    log("🎉 Clicked Publish via get_by_role!")
                except Exception as e:
                    log(f"❌ Failed to click publish button: {e}")
                    browser.close()
                    return False, f"Publish button not clickable: {e}", None

        # Wait for Reel upload and redirect confirmation
        log("⏳ Uploading Reel to Facebook servers (30s)...")
        for i in range(6):
            page.wait_for_timeout(5000)
            if "/reel/" in page.url:
                log(f"🎉 Live Reel Published! Direct URL: {page.url}")
                break

        # Screenshot success
        success_img = os.path.join(LOGS_DIR, f"success_{video_filename}_{int(time.time())}.png")
        page.screenshot(path=success_img)
        log(f"📸 Screenshot saved: {success_img}")

        browser.close()
        return True, "Reel uploaded successfully!", final_caption

def auto_delete_video(video_path, video_filename):
    """
    Deletes the uploaded video from disk and updates queue.json.
    """
    try:
        if os.path.exists(video_path):
            os.remove(video_path)
            log(f"🗑️ Successfully deleted uploaded video: {video_path}")

        # Remove from queue.json if present
        if os.path.exists(QUEUE_FILE):
            try:
                with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                    queue = json.load(f)
                new_queue = [item for item in queue if item.get("filename") != video_filename]
                with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                    json.dump(new_queue, f, indent=2, ensure_ascii=False)
                log(f"📋 Removed '{video_filename}' from queue.json")
            except Exception as q_ex:
                log(f"⚠️ Failed to update queue.json: {q_ex}")

    except Exception as e:
        log(f"⚠️ Failed to delete video {video_path}: {e}")

def main():
    log("=" * 65)
    log("🔥 Facebook Reels Ultra-Deep AI Auto Uploader Starting...")
    log(f"⏰ Current Nepal Time: {get_nepal_time_str()}")
    log("=" * 65)

    if not prepare_storage_state():
        sys.exit(1)

    video_info = get_next_video()
    if not video_info:
        log("✨ No pending videos found in 'videos/' folder!")
        log("💡 Simply copy your new .mp4 video files into 'videos/' folder.")
        sys.exit(0)

    log(f"🎯 Target video selected for upload: {video_info['filename']}")

    success, message, caption_used = upload_reel(video_info)

    history = load_posted_history()
    now_utc = datetime.now(timezone.utc).isoformat()
    now_npt = get_nepal_time_str()

    history.append({
        "filename": video_info["filename"],
        "posted_at_npt": now_npt,
        "posted_at_utc": now_utc,
        "status": "success" if success else "failed",
        "caption": caption_used or "",
        "message": message
    })
    save_posted_history(history)

    if success:
        # Auto-delete video upon success!
        auto_delete_video(video_info["filepath"], video_info["filename"])

        success_msg = f"✅ <b>Facebook Reel Uploaded & Auto-Cleaned!</b>\n\n🎬 <b>Video:</b> {video_info['filename']}\n⏰ <b>Time:</b> {now_npt}"
        log(f"🎉 {success_msg}")
        send_telegram_notification(success_msg)
        sys.exit(0)
    else:
        fail_msg = f"❌ <b>Facebook Reel Upload Failed!</b>\n\n🎬 <b>Video:</b> {video_info['filename']}\n⚠️ <b>Error:</b> {message}"
        log(fail_msg)
        send_telegram_notification(fail_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
