# Sightline AI

An AI-powered real-time accessibility assistant for visually impaired users
on video calls (Zoom, Teams, Google Meet). Existing screen readers
(VoiceOver, TalkBack) can't read live video call content — Sightline AI
fills that gap by describing what's visually on screen.

## Status

Day-1 MVP: a minimal proof of concept. Press Enter, get a screenshot of your
screen described aloud. No continuous monitoring, no call-app targeting, no
real-time pipeline yet — that comes after we confirm the AI descriptions are
actually useful.

## Roadmap

- [x] One-shot screenshot → Gemini → spoken description (macOS)
- [ ] Validate description quality with real users
- [ ] Target active call window instead of full screen
- [ ] Global hotkey instead of terminal prompt
- [ ] Continuous capture with frame-differential filtering
- [ ] On-device processing for privacy
- [ ] Windows support
- [ ] Mobile (Android via MediaProjection/AccessibilityService, iOS via ReplayKit)

## Setup

1. Get a free Gemini API key: https://aistudio.google.com/apikey
2. Clone this repo and run the launcher:

```bash
git clone https://github.com/meghasainath/sightline-AI.git
cd sightline-AI
export GEMINI_API_KEY="your-key-here"
./run.sh
```

The first run creates a virtual environment and installs dependencies
automatically. Later runs are instant.

### macOS permissions (one-time)

The app needs Terminal to have **Screen Recording** permission, since it
takes a screenshot of your screen:

**System Settings → Privacy & Security → Screen Recording → turn on Terminal**
(then fully quit and reopen Terminal).

macOS only for now (uses the built-in `screencapture` and `say` commands).

## Usage

Once running and you see `[Ready]`, press **Enter** whenever you want a
description of what's currently on screen — e.g. during a Zoom/Teams/Meet
call. Type `q` to quit.

Diagnostic flags:
```bash
python3 sightline.py --test-capture   # tests screen capture + permissions only
python3 sightline.py --test-speech    # tests text-to-speech only
```

## Design decisions

- **On-demand narration**, not proactive interruption — the user controls
  when they get a description, so it never talks over a presenter.
- **Visual-only descriptions** — never repeats what's being said aloud,
  since the user can already hear that.
- **Blocking speech output** — the app waits for a description to finish
  speaking before accepting the next input, so descriptions can't get cut
  off by a quick keypress.
- **Model fallback** — tries several Gemini model names in order
  (`gemini-2.5-flash`, `gemini-flash-latest`, `gemini-2.0-flash`,
  `gemini-3.8-flash`) so a single overloaded (503) or deprecated (404)
  model doesn't block the whole app.
- **On-device processing planned for later versions** — privacy and trust
  matter more than raw accuracy for this user base.
- Named after considering "InSight" first, moved to "Sightline" to avoid
  it sounding like "incite" when read aloud by a screen reader.

## Security note

If you ever paste your Gemini API key into a chat, terminal log, or shared
document, treat it as compromised and generate a new one at
https://aistudio.google.com/apikey.
