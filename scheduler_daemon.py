#!/usr/bin/env python3
"""
24/7 Nepal Time Local Scheduler Daemon
======================================
नेपाली समय अनुसार स्वचालित रूपमा रिल अपलोड गर्ने ब्याकग्राउन्ड सर्भिस:
- 07:00 AM NPT
- 01:00 PM NPT
- 04:00 PM NPT
- 07:00 PM NPT
"""

import time
import subprocess
import os
import sys
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADER_SCRIPT = os.path.join(BASE_DIR, "uploader.py")
NEPAL_TZ = timezone(timedelta(hours=5, minutes=45))

# Target Upload Times (Hour in 24h, Minute) in Nepal Time
TARGET_TIMES = [
    (7, 0),   # 07:00 AM
    (13, 0),  # 01:00 PM
    (16, 0),  # 04:00 PM
    (19, 0)   # 07:00 PM
]

def log(msg):
    now_npt = datetime.now(NEPAL_TZ).strftime("%Y-%m-%d %I:%M:%S %p NPT")
    print(f"[{now_npt}] {msg}", flush=True)

def run_uploader():
    log("🚀 Target schedule reached! Running uploader.py...")
    try:
        res = subprocess.run([sys.executable, UPLOADER_SCRIPT], cwd=BASE_DIR, capture_output=True, text=True)
        print(res.stdout)
        if res.stderr:
            print(res.stderr, file=sys.stderr)
        log(f"🏁 Uploader finished with exit code {res.returncode}")
    except Exception as e:
        log(f"❌ Execution error: {e}")

def main():
    log("=" * 60)
    log("🇳🇵 Facebook Reels Local Scheduler Daemon Started")
    log(f"⏰ Monitoring upload schedule at: 7:00 AM, 1:00 PM, 4:00 PM, 7:00 PM NPT")
    log("=" * 60)

    last_triggered_date_hour = None

    while True:
        now = datetime.now(NEPAL_TZ)
        cur_hour = now.hour
        cur_min = now.minute
        cur_date_str = now.strftime("%Y-%m-%d")

        for thour, tmin in TARGET_TIMES:
            # Check if within trigger window (exact minute match)
            if cur_hour == thour and cur_min == tmin:
                trigger_key = f"{cur_date_str}_{thour}_{tmin}"
                if last_triggered_date_hour != trigger_key:
                    last_triggered_date_hour = trigger_key
                    run_uploader()

        # Check every 25 seconds
        time.sleep(25)

if __name__ == "__main__":
    main()
