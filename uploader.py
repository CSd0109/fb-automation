#!/usr/bin/env python3
"""
Facebook Reels Auto Uploader (Personal Profile ID)
==================================================
Runs on GitHub Actions (or locally) at Nepali Times:
- 7:00 AM NPT
- 1:00 PM NPT
- 4:00 PM NPT
- 7:00 PM NPT

Automates posting Reels to personal Facebook profile using Playwright & Session State.
"""

import os
import sys
import json
import time
import glob
from datetime import datetime, timezone, timedelta
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

load_dotenv()

# Constants & Paths
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
    now_npt = datetime.now(NEPAL_TZ)
    return now_npt.strftime("%Y-%m-%d %I:%M:%S %p NPT")

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
            log("📱 Telegram notification sent successfully.")
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
    Finds the next unposted video from queue.json or videos/ folder.
    """
    history = load_posted_history()
    posted_filenames = {item.get("filename") for item in history if item.get("status") == "success"}

    # 1. Check queue.json if present
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                queue = json.load(f)
                for item in queue:
                    fname = item.get("filename")
                    full_path = os.path.join(VIDEOS_DIR, fname)
                    if fname and fname not in posted_filenames and os.path.exists(full_path):
                        return {
                            "filename": fname,
                            "filepath": full_path,
                            "caption": item.get("caption", ""),
                            "source": "queue.json"
                        }
        except Exception as e:
            log(f"⚠️ Error reading queue.json: {e}")

    # 2. Fallback to scanning videos/ directory
    supported_extensions = ("*.mp4", "*.mov", "*.webm", "*.mkv")
    video_files = []
    for ext in supported_extensions:
        video_files.extend(glob.glob(os.path.join(VIDEOS_DIR, ext)))
    
    video_files.sort() # alphabetical / FIFO order

    for vpath in video_files:
        vname = os.path.basename(vpath)
        if vname not in posted_filenames:
            return {
                "filename": vname,
                "filepath": vpath,
                "caption": "",
                "source": "videos_dir"
            }

    return None

def generate_ai_caption(video_path, video_filename):
    """
    Generates SEO viral caption with hashtags using Gemini API if available.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        log("ℹ️ No GEMINI_API_KEY found, using standard viral Nepali & English caption.")
        return f"✨ Watch till the end! 🔥\n\n#reels #fyp #nepal #trending #viral #fbreels #{video_filename.split('.')[0]}"

    try:
        from google import genai
        log("🤖 Gemini AI is generating viral SEO caption for Reel...")
        client = genai.Client(api_key=gemini_key)
        
        # Upload video to Gemini for multimodal analysis if small enough (<50MB)
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        if file_size_mb < 50:
            try:
                sample_file = client.files.upload(file=video_path)
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[
                        sample_file,
                        "Analyze this short video and write an ultra-engaging, viral Facebook Reel caption in Nepali and English with attractive emojis and high-ranking hashtags (like #fyp #reels #nepal #trending). Keep it under 50 words."
                    ]
                )
                caption = response.text.strip()
                log(f"✨ AI Generated Caption:\n{caption}")
                return caption
            except Exception as ex:
                log(f"⚠️ Gemini video upload failed, falling back to text prompt: {ex}")

        # Text prompt fallback
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                f"Write an ultra-engaging, viral Facebook Reel caption for a video named '{video_filename}'. Include Nepali/English catchy hook, emojis, and viral hashtags (like #fyp #reels #nepal #trending). Keep it under 50 words."
            ]
        )
        caption = response.text.strip()
        log(f"✨ AI Generated Caption:\n{caption}")
        return caption

    except Exception as e:
        log(f"⚠️ Gemini caption generation failed: {e}")
        return f"✨ Amazing Reel! Like, Comment & Share 🔥\n\n#reels #nepal #trending #fyp #viral"

def prepare_storage_state():
    """
    Ensures facebook_session.json exists, pulling from FB_STORAGE_STATE secret if available.
    """
    env_state = os.getenv("FB_STORAGE_STATE")
    if env_state and env_state.strip():
        try:
            state_data = json.loads(env_state.strip())
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(state_data, f)
            log("✅ Loaded session state from FB_STORAGE_STATE secret.")
            return True
        except Exception as e:
            log(f"⚠️ Failed to parse FB_STORAGE_STATE secret JSON: {e}")

    if os.path.exists(SESSION_FILE):
        log(f"✅ Using local session file: {SESSION_FILE}")
        return True

    log("❌ ERROR: No Facebook session found! Please run 'save_session.py' locally or add 'FB_STORAGE_STATE' to GitHub Secrets.")
    return False

def upload_reel(video_info):
    """
    Automates uploading a single video to Facebook Reels on Personal ID using Playwright.
    """
    video_path = video_info["filepath"]
    video_filename = video_info["filename"]
    caption = video_info["caption"] or generate_ai_caption(video_path, video_filename)

    log(f"🎬 Starting upload for video: {video_filename} ({os.path.getsize(video_path) / (1024*1024):.2f} MB)")

    is_headless = os.getenv("HEADLESS", "true").lower() != "false"

    with sync_playwright() as p:
        # Launch Chromium with stealth evasion flags
        browser = p.chromium.launch(
            headless=is_headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
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

        # Apply stealth script
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        log("🌐 Navigating to Facebook Reels Creation Page (https://www.facebook.com/reels/create)...")
        page.goto("https://www.facebook.com/reels/create", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        # Check if redirected to login
        current_url = page.url
        if "login" in current_url or "checkpoint" in current_url:
            screenshot_path = os.path.join(LOGS_DIR, f"login_required_{int(time.time())}.png")
            page.screenshot(path=screenshot_path)
            error_msg = "❌ Facebook Session Expired! Please re-run save_session.py and update FB_STORAGE_STATE in GitHub Secrets."
            log(error_msg)
            send_telegram_notification(f"🚨 <b>Facebook Reel Upload Failed!</b>\n\n{error_msg}")
            browser.close()
            return False, error_msg

        log("📤 Locating file upload input...")
        # Locate input[type="file"]
        file_input_selector = 'input[type="file"]'
        try:
            page.wait_for_selector(file_input_selector, state="attached", timeout=20000)
            file_input = page.locator(file_input_selector).first
            file_input.set_input_files(video_path)
            log("✅ Video file attached to upload input!")
        except Exception as ex:
            log(f"⚠️ Standard file input wait failed: {ex}. Attempting direct file chooser...")
            # Try file chooser trigger if needed
            try:
                with page.expect_file_chooser(timeout=10000) as fc_info:
                    page.locator('div[role="button"]:has-text("Add Video"), div[role="button"]:has-text("भिडियो थप्नुहोस्"), [aria-label*="Add video"]').first.click()
                file_chooser = fc_info.value
                file_chooser.set_files(video_path)
                log("✅ Video file attached via file chooser!")
            except Exception as fc_ex:
                log(f"❌ Failed to attach video: {fc_ex}")
                page.screenshot(path=os.path.join(LOGS_DIR, f"upload_error_{int(time.time())}.png"))
                browser.close()
                return False, f"Failed to attach video: {fc_ex}"

        # Wait for Facebook to process video preview
        log("⏳ Waiting for video preview & processing...")
        page.wait_for_timeout(8000)

        # Step 1: Click "Next" / "अर्को" button
        next_button_selectors = [
            'div[aria-label="Next"]',
            'div[aria-label="अर्को"]',
            'div[role="button"]:has-text("Next")',
            'div[role="button"]:has-text("अर्को")',
            'button:has-text("Next")',
            'button:has-text("अर्को")'
        ]

        def click_next_if_visible():
            for selector in next_button_selectors:
                try:
                    loc = page.locator(selector).first
                    if loc.is_visible(timeout=3000):
                        loc.click()
                        log(f"➡️ Clicked 'Next' button ({selector})")
                        page.wait_for_timeout(3000)
                        return True
                except Exception:
                    continue
            return False

        # Click Next (from Upload Step to Audio/Trim Step)
        if not click_next_if_visible():
            log("⚠️ 'Next' button not immediately found, waiting 5 more seconds for video processing...")
            page.wait_for_timeout(5000)
            click_next_if_visible()

        # Step 2: Audio/Trim to Details (If another "Next" exists)
        page.wait_for_timeout(3000)
        click_next_if_visible()

        # Step 3: Enter Caption / Description
        log("✍️ Entering Reel caption...")
        page.wait_for_timeout(2000)
        
        caption_selectors = [
            'div[aria-label*="Describe your reel"]',
            'div[aria-label*="आफ्नो रिल"]',
            'div[aria-label*="Write a description"]',
            'div[role="textbox"]',
            'div[contenteditable="true"]',
            'textarea'
        ]

        caption_entered = False
        for c_sel in caption_selectors:
            try:
                loc = page.locator(c_sel).first
                if loc.is_visible(timeout=3000):
                    loc.click()
                    page.wait_for_timeout(500)
                    # Type caption smoothly
                    page.keyboard.type(caption, delay=15)
                    log(f"✅ Caption filled into ({c_sel})")
                    caption_entered = True
                    break
            except Exception:
                continue

        if not caption_entered:
            log("⚠️ Could not find description textbox selector, attempting direct keyboard typing...")
            try:
                page.keyboard.press("Tab")
                page.keyboard.type(caption, delay=15)
            except Exception as ex:
                log(f"⚠️ Fallback caption typing error: {ex}")

        page.wait_for_timeout(3000)

        # Step 4: Click "Publish" / "पोस्ट" / "प्रकाशित गर्नुहोस्"
        log("🚀 Clicking 'Publish' button...")
        publish_selectors = [
            'div[aria-label="Publish"]',
            'div[aria-label="प्रकाशित गर्नुहोस्"]',
            'div[aria-label="Post"]',
            'div[role="button"]:has-text("Publish")',
            'div[role="button"]:has-text("प्रकाशित गर्नुहोस्")',
            'div[role="button"]:has-text("Post")',
            'div[role="button"]:has-text("पोस्ट गर्नुहोस्")',
            'button:has-text("Publish")',
            'button:has-text("Post")'
        ]

        published_clicked = False
        for p_sel in publish_selectors:
            try:
                loc = page.locator(p_sel).first
                if loc.is_visible(timeout=4000):
                    loc.click()
                    log(f"🎉 Clicked Publish button ({p_sel})!")
                    published_clicked = True
                    break
            except Exception:
                continue

        if not published_clicked:
            # Look for any button with Publish text
            log("⚠️ Searching for fallback publish elements...")
            try:
                page.get_by_role("button", name="Publish").click(timeout=5000)
                published_clicked = True
                log("🎉 Clicked Publish via get_by_role!")
            except Exception as e:
                log(f"❌ Could not click publish button: {e}")
                screenshot_err = os.path.join(LOGS_DIR, f"publish_button_missing_{int(time.time())}.png")
                page.screenshot(path=screenshot_err)
                browser.close()
                return False, f"Could not find publish button: {e}"

        # Wait for video upload to finalize
        log("⏳ Waiting for Reel upload & publishing confirmation...")
        page.wait_for_timeout(20000) # Give Facebook 20s to complete upload

        # Save success screenshot
        success_screenshot = os.path.join(LOGS_DIR, f"published_{video_filename}_{int(time.time())}.png")
        page.screenshot(path=success_screenshot)
        log(f"📸 Saved screenshot: {success_screenshot}")

        browser.close()
        return True, "Reel published successfully!"

def main():
    log("=" * 60)
    log("🔥 Facebook Reels Auto Uploader Starting...")
    log(f"⏰ Current Nepal Time: {get_nepal_time_str()}")
    log("=" * 60)

    # 1. Verify Facebook session
    if not prepare_storage_state():
        sys.exit(1)

    # 2. Get next video to upload
    video_info = get_next_video()
    if not video_info:
        log("✨ No pending videos found to upload! Everything is up-to-date.")
        log("💡 To upload new reels, simply place your .mp4 files into the 'videos/' folder.")
        sys.exit(0)

    log(f"🎯 Target video selected: {video_info['filename']}")

    # 3. Perform upload
    success, message = upload_reel(video_info)

    # 4. Record history
    history = load_posted_history()
    now_utc = datetime.now(timezone.utc).isoformat()
    now_npt = get_nepal_time_str()

    history.append({
        "filename": video_info["filename"],
        "posted_at_npt": now_npt,
        "posted_at_utc": now_utc,
        "status": "success" if success else "failed",
        "caption": video_info.get("caption", ""),
        "message": message
    })
    save_posted_history(history)

    if success:
        success_msg = f"✅ <b>Facebook Reel Uploaded Successfully!</b>\n\n🎬 <b>Video:</b> {video_info['filename']}\n⏰ <b>Time:</b> {now_npt}"
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
