#!/usr/bin/env python3
"""
Sightline AI — Day-1 MVP Accessibility Tool for Visually Impaired Users.
Captures screen content, analyzes it with Gemini, and speaks the description aloud.
"""

import os
import sys
import time
import re
import argparse
import tempfile
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Try a list of models in order, falling back if one is overloaded/unavailable.
CANDIDATE_MODELS = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.0-flash", "gemini-3.8-flash"]


class SpeechEngine:
    def __init__(self):
        self._current_process = None

    def stop(self):
        if self._current_process and self._current_process.poll() is None:
            try:
                self._current_process.terminate()
                self._current_process.wait(timeout=1.0)
            except Exception:
                try:
                    self._current_process.kill()
                except Exception:
                    pass
        self._current_process = None

    def speak(self, text: str, wait: bool = False):
        self.stop()
        if not text or not text.strip():
            return
        cleaned = self._clean_for_speech(text)
        try:
            cmd = ["say", "-r", "190", cleaned]
            if wait:
                subprocess.run(cmd, check=False)
            else:
                self._current_process = subprocess.Popen(cmd)
        except FileNotFoundError:
            print("[Warning] macOS 'say' command not found. Cannot speak aloud.")
        except Exception as e:
            print(f"[Warning] Speech error: {e}")

    @staticmethod
    def _clean_for_speech(text: str) -> str:
        cleaned = re.sub(r"[*_~`]+", " ", text)
        cleaned = re.sub(r"^#+\s*", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"^\s*[-+*]\s+", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned


def capture_screen(output_path: str) -> bool:
    try:
        res = subprocess.run(
            ["screencapture", "-x", "-m", output_path],
            capture_output=True, text=True, check=False
        )
        if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        res2 = subprocess.run(
            ["screencapture", "-x", output_path],
            capture_output=True, text=True, check=False
        )
        return res2.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0
    except Exception as e:
        print(f"[Error] screencapture failed: {e}")
        return False


def get_gemini_client(api_key: str):
    from google import genai
    return genai.Client(api_key=api_key)


SYSTEM_PROMPT = """
You are Sightline AI, an accessibility tool for visually impaired professionals during video calls (Zoom, Google Meet, Microsoft Teams) or computer work.
You are looking at a screenshot of the user's screen.
Provide a concise, direct, spoken description designed to be read aloud by text-to-speech.

Guidelines:
1. Identify the key context: what is being shared? (e.g., "A presentation slide titled...", "A spreadsheet detailing quarterly sales...", "A software architecture diagram showing...", "A video call window with chat").
2. Describe the primary visual content: read out main headlines, key bullet points, or the main trend shown in charts/graphs.
3. Keep it brief and focused (approximately 3 to 5 sentences). Visually impaired users need immediate, high-signal summaries without overwhelming clutter.
4. Output strictly plain conversational text. Do NOT use markdown symbols, bullet points, asterisks, hashtags, or raw links, as they sound awkward when read by a screen reader.
"""


def describe_screen(client, image_path: str) -> str:
    """Send screenshot to Gemini and return the spoken description.
    Tries each candidate model in order until one succeeds (handles
    404 'model not found' and 503 'overloaded' by moving to the next)."""
    from PIL import Image
    from google.genai.errors import ClientError, ServerError

    last_error = None
    with Image.open(image_path) as img:
        for model_name in CANDIDATE_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        SYSTEM_PROMPT,
                        img,
                        "Describe what is currently visible and shared on this screen for a visually impaired user."
                    ]
                )
                return response.text.strip() if response.text else "No description received."
            except (ClientError, ServerError, Exception) as e:
                last_error = e
                print(f"[Info] Model '{model_name}' unavailable ({e}); trying next...")
                continue
    raise last_error if last_error else RuntimeError("All models failed.")


def setup_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and api_key.strip():
        return api_key.strip()

    env_file = Path(__file__).resolve().parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and api_key.strip():
            return api_key.strip()

    print("\n" + "=" * 60)
    print("  Sightline AI — Setup GEMINI_API_KEY")
    print("=" * 60)
    print("GEMINI_API_KEY environment variable is not set.")
    print("Get your free API key at: https://aistudio.google.com/app/apikey\n")
    try:
        user_input = input("Enter your Gemini API key (or press Ctrl+C to exit): ").strip()
        if not user_input:
            print("API key cannot be empty.")
            sys.exit(1)
        save = input("Would you like to save this key to .env for future sessions? [Y/n]: ").strip().lower()
        if save in ("", "y", "yes"):
            with open(env_file, "w") as f:
                f.write(f"GEMINI_API_KEY={user_input}\n")
            print(f"Saved key to {env_file}")
        return user_input
    except KeyboardInterrupt:
        print("\nExiting.")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Sightline AI — macOS Accessibility Screen Describer")
    parser.add_argument("--test-speech", action="store_true", help="Test audio text-to-speech output")
    parser.add_argument("--test-capture", action="store_true", help="Test screen capture without calling Gemini")
    parser.add_argument("--image", type=str, help="Describe an existing image file instead of taking a screenshot")
    args = parser.parse_args()

    speech = SpeechEngine()

    if args.test_speech:
        print("[Diagnostic] Testing macOS text-to-speech...")
        speech.speak("Sightline AI speech test. Audio output is working properly.", wait=True)
        print("[Diagnostic] Done.")
        return

    if args.test_capture:
        print("[Diagnostic] Testing macOS screen capture...")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            test_path = tf.name
        try:
            if capture_screen(test_path):
                from PIL import Image
                with Image.open(test_path) as im:
                    print(f"[Diagnostic] Screen capture SUCCESS! Resolution: {im.size[0]}x{im.size[1]} pixels.")
                speech.speak("Screen capture test succeeded.", wait=True)
            else:
                print("[Diagnostic] Screen capture failed. Ensure Screen Recording permission is enabled in System Settings.")
                speech.speak("Screen capture test failed. Please check permissions.", wait=True)
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)
        return

    print("""
================================================================
   Sightline AI — Accessibility Vision Assistant (Day-1 MVP)
   Audio: macOS Native Speech
================================================================
""")
    api_key = setup_api_key()

    if args.image:
        if not os.path.exists(args.image):
            print(f"[Error] Image file not found: {args.image}")
            return
        print("Initializing Gemini Client...")
        client = get_gemini_client(api_key)
        print(f"Analyzing {args.image}...")
        speech.speak("Analyzing image.")
        description = describe_screen(client, args.image)
        print("\nGemini Response:")
        print("-" * 60)
        print(description)
        print("-" * 60)
        speech.speak(description, wait=True)
        return

    print("Initializing Gemini Client...")
    try:
        client = get_gemini_client(api_key)
    except Exception as e:
        print(f"[Error] Failed to initialize Gemini client: {e}")
        speech.speak("Failed to initialize Gemini client. Please check your API key.", wait=True)
        sys.exit(1)

    print("\n[Ready] Sightline AI is listening.")
    print("  - Press [Enter] to capture and describe your screen")
    print("  - Type 'q' and press [Enter] to quit")
    print("  - Tip: Keep this terminal in the background or on a side screen while on your call.\n")

    speech.speak("Sightline AI is ready. Press enter to capture screen.")

    with tempfile.TemporaryDirectory() as tmpdir:
        screenshot_path = os.path.join(tmpdir, "sightline_capture.png")

        while True:
            try:
                cmd = input("[Sightline AI] Press [Enter] to capture (or 'q' to quit): ").strip()
                if cmd.lower() in ("q", "quit", "exit"):
                    print("Exiting Sightline AI. Goodbye!")
                    speech.speak("Goodbye.", wait=True)
                    break

                speech.stop()
                print("\n[1/3] Capturing screen...")

                time.sleep(0.3)

                success = capture_screen(screenshot_path)
                if not success:
                    err_msg = (
                        "Screen capture failed. macOS may require Screen Recording permission. "
                        "Please check System Settings > Privacy & Security > Screen Recording."
                    )
                    print(f"\n[Error] {err_msg}")
                    speech.speak("Screen capture failed. Please check screen recording permissions in System Settings.")
                    continue

                print("[2/3] Analyzing...")

                t0 = time.time()
                try:
                    description = describe_screen(client, screenshot_path)
                    elapsed = time.time() - t0
                    print(f"\n[3/3] Response ({elapsed:.2f}s):")
                    print("-" * 60)
                    print(description)
                    print("-" * 60 + "\n")

                    speech.speak(description, wait=True)

                except Exception as e:
                    print(f"\n[Error] Gemini API error: {e}")
                    speech.speak("Sorry, an error occurred while analyzing the screen with Gemini.", wait=True)

            except KeyboardInterrupt:
                print("\nInterrupted by user. Exiting.")
                speech.stop()
                break
            except Exception as e:
                print(f"\n[Unexpected Error]: {e}")


if __name__ == "__main__":
    main()
