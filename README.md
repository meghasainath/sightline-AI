# Sightline AI

An AI-powered real-time accessibility assistant for visually impaired users
on video calls (Zoom, Teams, Google Meet). Existing screen readers
(VoiceOver, TalkBack) can't read live video call content — Sightline AI
fills that gap by describing what's visually on screen.

## Status

Day-1 MVP: a minimal proof of concept. Press a key, get a screenshot of your
screen described aloud. No continuous monitoring, no call-app targeting, no
real-time pipeline yet — that comes after we confirm the AI descriptions are
actually useful.

## Roadmap

- [x] One-shot screenshot → Gemini Flash → spoken description (macOS)
- [ ] Validate description quality with real users
- [ ] Target active call window instead of full screen
- [ ] Global hotkey instead of terminal prompt
- [ ] Continuous capture with frame-differential filtering
- [ ] On-device processing for privacy
- [ ] Windows support
- [ ] Mobile (Android via MediaProjection/AccessibilityService, iOS via ReplayKit)

## Setup

```bash
pip3 install google-genai
export GEMINI_API_KEY="your-key-here"   # https://aistudio.google.com/apikey
python3 sightline_mvp.py
```

macOS only for now (uses the built-in `screencapture` and `say` commands).

## Design decisions

- **On-demand narration**, not proactive interruption — the user controls
  when they get a description, so it never talks over a presenter.
- **Visual-only descriptions** — never repeats what's being said aloud,
  since the user can already hear that.
- **On-device processing planned for later versions** — privacy and trust
  matter more than raw accuracy for this user base.
- Named after considering "InSight" first, moved to "Sightline" to avoid
  it sounding like "incite" when read aloud by a screen reader.
