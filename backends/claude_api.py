# [claude-code/claude-sonnet-4-6] Claude API harmonizer backend
# Sends melody + style to Claude, gets back SATB as structured JSON.
# Falls back to RuleBasedBackend if ANTHROPIC_API_KEY is not set.
import os
import json
import music21
from backends.rule_based import RuleBasedBackend

ERA_DESCRIPTIONS = {
    'classical': 'Classical period (Haydn/Mozart style): clear diatonic harmony, balanced voice leading, functional progressions',
    'baroque':   'Baroque style (Bach chorale style): strict voice leading, V7 cadences, suspensions, no parallel fifths or octaves',
    'romantic':  'Romantic period (Schubert/Brahms style): rich 7th chords, chromaticism, expressive inner voices',
    'jazz':      'Jazz harmony: 7th and 9th chords, ii-V-I progressions, chromatic voice leading, tritone substitutions',
}


def _midi_to_note(midi):
    return music21.pitch.Pitch(midi).nameWithOctave


def _beat_duration(midi_start_end, bpm):
    _, st, en = midi_start_end
    beat_sec = 60.0 / bpm
    dur_sec = max(en - st, 0.25)
    return max(0.5, round((dur_sec / beat_sec) * 2) / 2)


class ClaudeBackend:
    def harmonize(self, melody, tonic, mode, era, bpm):
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            print('[ClaudeBackend] ANTHROPIC_API_KEY not set, falling back to rule-based')
            return RuleBasedBackend().harmonize(melody, tonic, mode, era, bpm)

        try:
            import anthropic
        except ImportError:
            print('[ClaudeBackend] anthropic package not installed, falling back to rule-based')
            return RuleBasedBackend().harmonize(melody, tonic, mode, era, bpm)

        era_desc = ERA_DESCRIPTIONS.get(era, ERA_DESCRIPTIONS['classical'])

        # build melody description for the prompt
        melody_lines = []
        for midi, st, en in melody:
            ql = _beat_duration((midi, st, en), bpm)
            melody_lines.append(f'  {_midi_to_note(midi)} ({ql} beats)')
        melody_str = '\n'.join(melody_lines)

        prompt = f"""You are a music theorist and expert harmonist. Harmonize the following soprano melody in SATB (Soprano, Alto, Tenor, Bass) format.

Key: {tonic} {mode}
Style: {era_desc}

Soprano melody (your soprano voice MUST use exactly these pitches and durations):
{melody_str}

Rules:
- Soprano must match the given melody exactly (same pitches and durations)
- Alto range: G3–C5
- Tenor range: C3–G4
- Bass range: E2–C4
- Avoid parallel fifths and octaves between any two voices
- Prefer stepwise motion in inner voices
- Bass should outline the harmonic progression clearly

Return ONLY valid JSON in this exact format, no explanation:
{{
  "soprano": [{{"pitch": "C4", "quarterLength": 1.0}}, ...],
  "alto":    [{{"pitch": "G3", "quarterLength": 1.0}}, ...],
  "tenor":   [{{"pitch": "E3", "quarterLength": 1.0}}, ...],
  "bass":    [{{"pitch": "C3", "quarterLength": 1.0}}, ...]
}}

Each list must have exactly {len(melody)} notes."""

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model='claude-opus-4-6',
            max_tokens=4096,
            messages=[{'role': 'user', 'content': prompt}],
        )

        raw = message.content[0].text.strip()

        # strip markdown code fences if present
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]

        satb = json.loads(raw)

        # validate structure
        for voice in ('soprano', 'alto', 'tenor', 'bass'):
            if voice not in satb:
                raise ValueError(f'Claude response missing voice: {voice}')
            if len(satb[voice]) != len(melody):
                raise ValueError(f'{voice} has {len(satb[voice])} notes, expected {len(melody)}')

        return satb
