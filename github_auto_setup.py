#!/usr/bin/env python3
"""
GitHub Auto Setup Assistant
===========================
Opens a visible browser on your desktop screen to help you:
1. Log into GitHub (if not already logged in)
2. Automatically create 'facebook-reels-uploader' repository
3. Automatically add FB_STORAGE_STATE and GEMINI_API_KEY secrets
4. Push the project so GitHub Actions runs 24/7!
"""

import os
import sys
import json
import time
import subprocess
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE = os.path.join(BASE_DIR, "facebook_session.json")

with open(SESSION_FILE, "r") as f:
    fb_session_str = f.read().strip()

print("=" * 65)
print("🚀 GitHub Actions 24/7 Auto Setup Assistant")
print("=" * 65)
print("१. स्क्रिनमा एउटा ब्राउजर खुल्नेछ।")
print("२. यदि GitHub लगइन छैन भने लगइन गर्नुहोस्।")
print("३. लगइन भएपछि यो टुलले आफैँ Repo बनाउनेछ र Secrets हाल्नेछ!")
print("=" * 65)

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
    )
    context = browser.new_context(viewport=None)
    page = context.new_page()

    page.goto("https://github.com/login")
    print("\n⏳ कृपया स्क्रिनमा खुलेको ब्राउजरमा GitHub लगइन गर्नुहोस्...")
    
    # Wait until user is logged in
    while True:
        if "github.com/login" not in page.url and "github.com/session" not in page.url:
            print("✅ GitHub लगइन प्रमाणीकरण भयो!")
            break
        page.wait_for_timeout(2000)

    # Get logged in username
    page.goto("https://github.com/", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    # Go to create repo
    REPO_NAME = "facebook-reels-auto-uploader"
    print(f"📦 नयाँ Private Repository '{REPO_NAME}' बनाउँदैछ...")
    page.goto("https://github.com/new", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    try:
        page.locator('input[aria-label="Repository"], [data-testid="repository-name-input"]').first.fill(REPO_NAME)
        page.wait_for_timeout(1000)
        page.locator('input[type="radio"][value="private"]').first.click()
        page.wait_for_timeout(1000)
        page.locator('button:has-text("Create repository")').first.click()
        page.wait_for_timeout(5000)
        print("🎉 Repository तयार भयो!")
    except Exception as e:
        print(f"Repo creation note: {e}")

    # Add Secret FB_STORAGE_STATE
    print("🔐 GitHub Secret (FB_STORAGE_STATE) थप्दैछ...")
    page.goto(f"https://github.com/CSd0109/{REPO_NAME}/settings/secrets/actions/new", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    try:
        page.locator('input#secret_name, input[name="secret_name"]').first.fill("FB_STORAGE_STATE")
        page.locator('textarea#secret_value, textarea[name="secret_value"]').first.fill(fb_session_str)
        page.wait_for_timeout(1000)
        page.locator('button:has-text("Add secret")').first.click()
        page.wait_for_timeout(3000)
        print("✅ FB_STORAGE_STATE सिक्रेट थपियो!")
    except Exception as ex:
        print(f"Secret adding note: {ex}")

    # Add Secret GEMINI_API_KEY
    print("🔐 GitHub Secret (GEMINI_API_KEY) थप्दैछ...")
    page.goto(f"https://github.com/CSd0109/{REPO_NAME}/settings/secrets/actions/new", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    try:
        page.locator('input#secret_name, input[name="secret_name"]').first.fill("GEMINI_API_KEY")
        page.locator('textarea#secret_value, textarea[name="secret_value"]').first.fill("")
        page.wait_for_timeout(1000)
        page.locator('button:has-text("Add secret")').first.click()
        page.wait_for_timeout(3000)
        print("✅ GEMINI_API_KEY सिक्रेट थपियो!")
    except Exception as ex:
        print(f"Secret adding note: {ex}")

    # Set Workflow Write Permissions
    print("⚙️ Actions Workflow Permissions सेट गर्दैछ...")
    page.goto(f"https://github.com/CSd0109/{REPO_NAME}/settings/actions", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    try:
        page.locator('input[value="write"]').first.click()
        page.wait_for_timeout(500)
        save_btn = page.locator('button:has-text("Save")').last
        if save_btn.is_enabled():
            save_btn.click()
            print("✅ Workflow Permissions सुरक्षित भयो!")
    except Exception as ex:
        print(f"Permissions note: {ex}")

    print("\n🎉 GitHub मा सम्पूर्ण सेटअप सम्पन्न भयो!")
    browser.close()

if __name__ == "__main__":
    main()
