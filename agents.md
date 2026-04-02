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
- `backend.py` — FastAPI app: Basic Pitch detection, deduplication, outlier filtering, quantization, key detection
- `harmonizer.py` — orchestrator: calls selected backend, converts output to music21 Score
- `backends/base.py` — HarmonizerBackend Protocol (swap backends here)
- `backends/claude_api.py` — Claude API backend (claude-opus-4-6); era + weirdness + voice_part aware
- `backends/rule_based.py` — local rule-based fallback; no API key needed
- `static/index.html` — all UI: BPM slider, metronome, backend toggle, voice selector, era, weirdness slider, OSMD rendering
- `requirements.txt` — Python dependencies (Python 3.11 required — 3.14 too new for ML deps)
- `.env` — ANTHROPIC_API_KEY goes here (gitignored)
- `tests/test_harmonizer.py` — unit tests for harmonizer (eras, voice ranges, BPM, fallbacks)
- `tests/test_backend.py` — integration tests using synthetic WAV files (no mic needed)
- `outputs/musicxml/` — generated MusicXML files (gitignored)

### Running tests
```bash
source .venv/bin/activate
python -m pytest tests/ -v   # 17 tests, all passing
```

---

## Known Limitations / Next Steps

- **Pitch detection accuracy** — Basic Pitch is good but not perfect for unaccompanied voice.
  Semitone errors on passing notes are common; errors track actual intonation (flat D → C#).
  Currently acceptable; revisit if accuracy becomes a blocker.
- **Duplicate note detection** — Basic Pitch splits sustained notes; mitigated with 150ms merge window.
  Occasionally 2-3 detections of the same attack still slip through.
- **Time signature hardcoded to 4/4** — acceptable for now.
- **No real-time display** — transcription happens after recording stops, not live.
- **Key detection confidence not surfaced** — music21 returns a confidence score we could show.
- **DeepBach as alternative backend** — would give genuine Bach-style voice leading locally,
  but only Bach. Use `backends/base.py` interface to add it.
- **LilyPond PDF export** — optional nice-to-have; `brew install lilypond` + music21 → PDF.

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

**What happened:**
- Replaced librosa.pyin with Basic Pitch (Spotify neural net) for pitch detection
- Added Basic Pitch parameter tuning: minimum_note_length=200ms, onset/frame thresholds raised
- Added outlier pitch filter (drops notes >2 octaves from median)
- Added consecutive same-pitch note merging (150ms gap threshold)
- Rebuilt venv on Python 3.11 (3.14 too new for ML packages)
- Implemented pluggable backend architecture (backends/base.py Protocol)
- Claude API backend (claude-opus-4-6): era + weirdness (1–100) + voice_part aware
- Rule-based backend kept as local fallback
- UI: BPM slider (replaces tap-tempo), metronome, backend toggle, voice part selector,
  era dropdown, weirdness slider (Claude only)
- Detected notes shown in UI for diagnostics
- End-to-end test: sang C major scale, got C D E F G F E C — working

**Next steps (suggested):**
- Try with cello (Seth's main instrument)
- Voice leading quality assessment with Claude backend
- Possibly snap detected pitches to key scale degrees (optional — current accuracy may be sufficient)
- DeepBach as local high-quality alternative backend
