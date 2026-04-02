# AGENTS.md — AI-leatoric

> This file is the shared memory and collaboration contract for all AI models working on this project.
> Read this at the start of every session, regardless of which tool you are.
> Update the "Work Log" section at the end of every session.

---

## Project Overview

**AI-leatoric** is a web app where a user sings or plays a melody (voice or cello),
and the app produces 4-part SATB sheet music from it.

The name is a pun on "aleatoric" (chance-based music composition) and "AI."

---

## How to run

```bash
cd ~/Library/CloudStorage/Dropbox/claude-projects/AI-leatoric
source .venv/bin/activate
uvicorn backend:app --port 8000
# open http://localhost:8000
```

Note: do NOT use `--reload` — the `.venv` directory is inside the project and triggers
constant restarts. If you need live reload during development, use
`--reload-exclude '.venv'` but expect a few spurious restarts on first launch.

---

## User Context

- **Developer:** Seth — comfortable in R and terminal, on macOS. No Python knowledge.
- **Instrument:** cello (important: pitch detection must handle low frequencies, C2 and up)
- **Philosophy:** vibe coding — agent does the work, Seth makes judgment calls
- **Preferred workflow:** Claude Code in terminal, push to setgree/AI-leatoric on GitHub

---

## Current Architecture (as of 2026-04-02)

### Stack
- **Backend:** Python, FastAPI (`backend.py`)
- **Pitch detection:** `librosa.pyin` (handles C2–C7, good for cello)
- **Harmonizer:** rule-based diatonic SATB (`harmonizer.py`) — supports major and natural minor
- **Key detection:** `music21` Krumhansl-Schmuckler analysis (`stream.analyze('key')`)
- **Sheet music rendering:** OpenSheetMusicDisplay (OSMD) via CDN — renders MusicXML in browser
- **Output:** MusicXML (viewable/playable in MuseScore) + inline browser rendering

### Flow
1. User taps beat (tap-tempo) to set BPM → average interval → quarter note grid
2. User clicks Record → MediaRecorder captures mic audio
3. User clicks Stop → audio sent to `/transcribe` as multipart form (with BPM)
4. Backend: pitch extraction (pyin) → onset segmentation → quantize to beat grid → key detection → SATB harmonization → write MusicXML
5. Frontend: fetch MusicXML → render with OSMD → show download link

### Key files
- `backend.py` — FastAPI app, pitch extraction, quantization, key detection
- `harmonizer.py` — rule-based SATB harmonizer (major + minor triads, voice range clamping)
- `static/index.html` — all UI: tap tempo, mic recording, OSMD rendering, download link
- `requirements.txt` — Python dependencies
- `outputs/musicxml/` — generated MusicXML files (gitignored)

---

## Known Limitations / Next Steps

- **Harmonizer is rule-based and conservative** — one triad per note, no voice leading smoothing.
  Good candidates for improvement: avoid parallel fifths/octaves, add passing tones, ii-V-I motion.
- **Key detection confidence is not surfaced** — music21 returns a confidence score we could show.
- **Time signature is hardcoded to 4/4** — acceptable for now.
- **Browser audio format** — MediaRecorder outputs webm (Chrome) or ogg (Firefox).
  librosa.load handles both via soundfile/audioread. No ffmpeg required currently.
- **No real-time display** — transcription happens after recording stops, not live.
- **Era / outeredness sliders** — conceived in original vision, not yet implemented.
  Would map to harmonization style (baroque voice leading rules, jazz extensions, etc.)

---

## Multi-Model Collaboration Convention

### Signing Your Work

All models must sign every function or significant block:

```python
# [claude-code/claude-sonnet-4-6] what this does and why
```

```javascript
// [claude-code/claude-sonnet-4-6] what this does and why
```

### Git Commit Convention

```
[claude-code/claude-sonnet-4-6] type: description
```

### Rules for All Models

1. **Read this file first.**
2. **Sign your work.**
3. **Don't add new dependencies without a one-line justification.**
4. **Don't delete another model's signed code without a comment explaining why.**
5. **Update the Work Log below** at the end of your session.
6. **If something is broken or uncertain**, mark it `# TODO [tool/model]: description`.
7. **Prefer simple over clever.** This is a creative tool, not a production system.
8. **Ask Seth** about output format or UX changes before building them.

---

## Work Log

*Append after every session. Do not overwrite previous entries.*

---

### [human + claude.ai/claude-sonnet-4-6] — 2026-02-22

**What happened:**
- Project conceived and named
- Explored ml5 PitchDetection — found octave errors at low frequencies (cello C-string ~73Hz)
- Identified Basic Pitch (Spotify) as better, but librosa.pyin was used in practice
- Initial scaffold: FastAPI backend, rule-based harmonizer, sine-wave synth, file-upload UI
- Pushed to GitHub: https://github.com/setgree/AI-leatoric
- Paused to hand off to Kilo.ai (never successfully used)

---

### [claude-code/claude-sonnet-4-6] — 2026-04-02

**What happened:**
- Resumed project; Seth confirmed the goal: sing/play → 4-part SATB sheet music in browser
- Replaced file-upload UI with MediaRecorder mic capture (Record/Stop)
- Added tap-tempo: user taps 4+ times → BPM detected → passed to backend
- Added onset quantization to eighth-note grid at tapped BPM
- Fixed quarterLength bug in harmonizer (was using raw seconds instead of beats)
- Added SATB voice range clamping (soprano C4–G5, alto G3–C5, tenor C3–G4, bass E2–C4)
- Added auto key detection via music21 Krumhansl-Schmuckler; key shown in UI
- Added minor key triads to harmonizer
- Replaced audio playback with OSMD inline sheet music rendering
- Added MusicXML download link (for MuseScore playback)
- Removed synth.py (was deleted, no longer needed)
- Committed and pushed all changes

**Decisions made:**
- OSMD for browser rendering (takes MusicXML we already produce — no format conversion needed)
- MuseScore for playback (Seth opens MusicXML there)
- Basic Pitch not yet adopted — librosa.pyin is good enough for now, revisit if octave errors appear
- LilyPond PDF export noted as optional future feature

**Next steps (suggested):**
- Test end-to-end with actual cello/voice input
- Voice leading improvements (avoid parallel fifths, smoother motion)
- Expose key detection confidence score in UI
- Consider era/outeredness sliders (original vision)
