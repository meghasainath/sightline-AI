#!/usr/bin/env python3
"""
Sightline AI — Day-1 MVP

The smallest useful test of the core idea: press a key, take one screenshot
of your screen (meant to be used while a call window is active/focused),
send it to Gemini Flash, get back a short spoken description of what's
visually on screen right now.

No continuous capture, no frame-diffing, no real app window targeting yet —
just: "what's on my screen, read it to me."

SETUP (one-time):
  1. pip3 install google-genai
  2. Get a free Gemini API key: https://aistudio.google.com/apikey
  3. Set it as an environment variable so it's never hardcoded in this file:
       export GEMINI_API_KEY="your-key-here"
     (Add that line to your ~/.zshrc to make it permanent.)

RUN:
  python3 sightline_mvp.py

USAGE:
  - The script waits for you to press Enter.
  - Each time you press Enter, it takes a screenshot and speaks a description.
  - Press Ctrl+C to quit.

This is macOS-only for now (uses the built-in `screencapture` and `say`
commands — no extra audio libraries needed, and it respects whatever
system voice you already have set in System Settings > Accessibility).
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Missing dependency. Run: pip3 install google-genai")
    sys.exit(1)

SYSTEM_PROMPT = (
    "You are a real-time visual accessibility assistant for a visually "
    "impaired person on a video call. You are shown a single screenshot "
    "of their current screen. In 1-2 short sentences, describe only the "
    "meaningful visual content: slide text, charts, shared documents, or "
    "on-screen text. Ignore window chrome, menu bars, icons, and other "
    "static UI elements. Be concise and speak as if reading it aloud to "
    "someone who cannot see the screen."
)


def check_macos():
    if sys.platform != "darwin":
        print("This MVP script currently only supports macOS "
              "(it uses the `screencapture` and `say` commands).")
        sys.exit(1)


def take_screenshot() -> Path:
    """Captures the whole screen to a temp PNG file and returns its path."""
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    # -x: no sound, -T0: no delay, captures the main display
    subprocess.run(["screencapture", "-x", "-T0", path], check=True)
    return Path(path)


def describe_image(client: "genai.Client", image_path: Path) -> str:
    image_bytes = image_path.read_bytes()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            "Describe what's visually on this screen right now.",
        ],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=150,
        ),
    )
    return response.text.strip()


def speak(text: str):
    print(f"\n🗣️  {text}\n")
    subprocess.run(["say", text])


def main():
    check_macos()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY environment variable not set.")
        print('Run: export GEMINI_API_KEY="your-key-here"')
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    print("Sightline AI — Day-1 MVP")
    print("Press Enter to capture and describe your screen. Ctrl+C to quit.\n")

    try:
        while True:
            input("Press Enter when ready...")
            screenshot_path = take_screenshot()
            try:
                print("Thinking...")
                description = describe_image(client, screenshot_path)
                speak(description)
            finally:
                screenshot_path.unlink(missing_ok=True)
    except KeyboardInterrupt:
        print("\nGoodbye.")


if __name__ == "__main__":
    main()
