#!/usr/bin/env python3
"""
Facebook Session Saver
======================
यो स्क्रिप्ट चलाएर तपाईँले आफ्नो कम्प्युटरमा एक पटक फेसबुक लगइन गर्नुहुनेछ।
यसले लगइन सेसन (Cookies & LocalStorage) लाई 'facebook_session.json' फाइलमा सुरक्षित गर्छ।
त्यसपछि यो JSON फाइलको डेटा GitHub Repository को Secrets (FB_STORAGE_STATE) मा राखेपछि
GitHub Actions ले २४/७ बिना पासवर्ड तपाईँको आइडीमा रिल अपलोड गर्न सक्छ।
"""

import os
import json
import time
from playwright.sync_api import sync_playwright

SESSION_FILE = "facebook_session.json"

def main():
    print("=" * 65)
    print("🚀 Facebook Session Saver - Setup Tool")
    print("=" * 65)
    print("1. एउटा नयाँ Chromium ब्राउजर खुल्नेछ।")
    print("2. कृपया त्यहाँ आफ्नो व्यक्तिगत फेसबुक आइडी (Personal ID) लगइन गर्नुहोस्।")
    print("3. लगइन भइसकेपछि (र 2FA कोड हालेपछि) यो टर्मिनलमा आएर ENTER थिच्नुहोस्।")
    print("=" * 65)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )
        
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        )
        
        page = context.new_page()
        print("\n🌐 फेसबुक लगइन पेज खोल्दैछ...")
        page.goto("https://www.facebook.com")

        print("\n⏳ कृपया ब्राउजरमा फेसबुक लगइन गर्नुहोस्...")
        print("👉 लगइन पूरा भएपछि यहाँ फर्केर 'ENTER' थिच्नुहोस्...")
        try:
            input()
        except KeyboardInterrupt:
            print("\nरद्द गरियो!")
            browser.close()
            return

        print("🔍 लगइन प्रमाणीकरण गर्दै...")
        # Check if c_user cookie exists
        cookies = context.cookies()
        c_user = next((c for c in cookies if c.get("name") == "c_user"), None)
        
        if c_user:
            print(f"✅ सफल लगइन! Facebook User ID (c_user): {c_user['value']}")
        else:
            print("⚠️ 'c_user' कुकी फेला परेन। तैपनि सेसन सेभ गरिँदैछ...")

        # Test navigating to Reels creator page
        print("🌐 Reels Creator पेज परीक्षण गर्दै...")
        page.goto("https://www.facebook.com/reels/create", timeout=30000)
        page.wait_for_timeout(3000)

        # Save storage state
        context.storage_state(path=SESSION_FILE)
        print(f"\n🎉 सेसन सफलतापूर्वक सेभ भयो: '{SESSION_FILE}'")

        browser.close()

    print("\n" + "=" * 65)
    print("📋 अब GitHub Actions को लागि के गर्ने?")
    print("=" * 65)
    print(f"1. '{SESSION_FILE}' फाइल खोल्नुहोस् र सम्पूर्ण JSON कोड कपि गर्नुहोस्।")
    print("2. आफ्नो GitHub Repository मा जानुहोस् -> Settings -> Secrets and variables -> Actions")
    print("3. 'New repository secret' मा क्लिक गर्नुहोस्:")
    print("   - Name: FB_STORAGE_STATE")
    print(f"   - Value: (कपि गरेको '{SESSION_FILE}' को सम्पूर्ण JSON टेक्स्ट पेस्ट गर्नुहोस्)")
    print("4. 'Add secret' थिच्नुहोस्!")
    print("=" * 65)

if __name__ == "__main__":
    main()
