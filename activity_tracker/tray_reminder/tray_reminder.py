from winotify import Notification, audio
import webbrowser
import json
import time
from pathlib import Path

SETTINGS_FILE = Path("data/settings.json")
STREAMLIT_URL = "http://localhost:8501"

print("✅ Activity Tracker tray reminder running...")

while True:
    try:
        # Read settings safely
        try:
            settings = json.load(open(SETTINGS_FILE))
            mins = int(settings.get("popup_min", 5))
        except Exception:
            mins = 5  # fallback

        # Create tray notification
        toast = Notification(
            app_id="Activity Tracker",
            title="Log now?",
            msg="Click here to open Activity Tracker",
            duration="short"   # auto hides (approx 5 sec)
        )

        toast.set_audio(audio.Default, loop=False)
        toast.add_actions(label="Open App", launch=STREAMLIT_URL)

        # Show tray popup
        toast.show()

        # Wait for next reminder interval
        time.sleep(mins * 60)

    except Exception as e:
        print("Tray Error:", e)
        time.sleep(60)
