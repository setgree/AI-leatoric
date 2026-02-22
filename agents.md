# AGENTS.md — AI-leatoric

> This file is the shared memory and collaboration contract for all AI models working on this project.
> Read this at the start of every session, regardless of which tool you are.
> Update the "Work Log" section at the end of every session.

---

## Project Overview

**AI-leatoric** is an app where a user sings a melody into their microphone, the app detects and displays the notes in real time (e.g. "A3", "D2"), and then generates variations of the recorded phrase using two parameters:

- **Era** — constrains the style of variation (e.g. baroque, jazz, atonal, contemporary)
- **Outeredness** — controls how far the variation drifts from the original (subtle embellishment → radical transformation)

The name is a pun on "aleatoric" (chance-based music composition) and "AI."

---

## Technical Context

- **Developer:** non-expert, comfortable in R and terminal, on macOS
- **Philosophy:** exploratory / vibe coding — don't over-engineer, don't introduce frameworks without a good reason
- **Input:** microphone audio
- **Core challenge:** accurate pitch detection including low octaves (models like CREPE/ml5 struggle below ~100Hz)
- **Preferred pitch detection:** Basic Pitch (Spotify, Python) is preferred over ml5 for octave accuracy
- **Output format:** TBD — could be audio playback, MIDI, piano roll, or just note names on screen. Ask the user if unclear.

---

## Multi-Model Collaboration Convention

This project is being built by multiple AI models across multiple tools (Kilo, Claude Code, GitHub Copilot, and others). To maintain accountability and traceability:

### Signing Your Work

**All models must sign every function, component, and significant block they write**, using this format in comments:

```
# [tool/model] description of what this does and why
```

Examples:
```python
# [claude-code/claude-sonnet-4-5] pitch-to-note conversion using A4=440Hz as reference
def hz_to_note_name(freq):
    ...
```

```javascript
// [kilo/claude-haiku-4-5] UI slider component for "outeredness" parameter
```

```
// [copilot/gpt-4o] autocompleted helper — review carefully
```

### Git Commit Convention

```
[tool/model] type: description

e.g.
[claude-code] feat: add Basic Pitch integration for low-octave detection
[kilo/sonnet] fix: octave disambiguation heuristic for sub-100Hz input
[copilot] refactor: extract note utils — verify before merging
```

### Rules for All Models

1. **Read this file first.** Don't start building without understanding what exists.
2. **Sign your work** as described above. No unsigned code.
3. **Don't introduce a new framework, dependency, or language without a one-line justification** in a comment or in this file.
4. **Don't delete or overwrite another model's signed code** without noting why in a comment.
5. **Update the Work Log below** at the end of your session — what you did, what you decided, what's next.
6. **If something is broken or uncertain, say so** in a `# TODO [tool/model]:` comment rather than silently leaving it.
7. **Prefer simple over clever.** This is a creative tool, not a production system.
8. **Ask the user** about output format (audio/MIDI/visual) before building it — it hasn't been decided yet.

---

## Current State

**Status:** Pre-code. No files written yet.

**Decisions made so far (in conversation, not yet in code):**
- Basic Pitch (Python) preferred over ml5 for pitch detection accuracy
- Multi-model collaboration with signing convention established
- Output format TBD — user to decide
- Keep it simple, no unnecessary frameworks

**Known issues / gotchas:**
- ml5/CREPE unreliable below ~100Hz (tested: low D on cello C-string at ~73Hz returned wrong octave)
- Whatever handles pitch detection needs to be robust to a user with perfect pitch who will notice octave errors

---

## Work Log

*Append to this after every session. Do not overwrite previous entries.*

---

### [human + claude.ai/claude-sonnet-4-6] — 2026-02-22

**What happened:**
- Project conceived and named
- Explored ml5 PitchDetection via p5js editor — found octave detection unreliable at low frequencies
- Identified Basic Pitch (Spotify, Python) as better foundation
- Decided on multi-model workflow with AGENTS.md as shared memory
- Established signing convention for code and commits
- MVP defined: mic input → real-time note name display → record phrase → generate variations with era + outeredness parameters

**Decisions made:**
- Use Basic Pitch over ml5 for pitch detection
- Output format not yet decided — ask user
- Keep stack simple, no frameworks unless justified

**Next steps:**
- First coding session: get mic input → note name displaying on screen
- Decide on output format (audio playback / MIDI / visual)
- Choose starting tool (Kilo recommended, credits available)

--- 