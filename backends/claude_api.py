# [claude-code/claude-sonnet-4-6] Claude API harmonizer backend with weirdness + voice_part support
import os
import json
import music21
from backends.rule_based import RuleBasedBackend, VOICE_RANGES

ERA_DESCRIPTIONS = {
    'classical': 'Classical period (Haydn/Mozart): clear diatonic harmony, balanced voice leading, functional progressions',
    'baroque':   'Baroque (Bach chorale style): strict voice leading, V7 cadences, suspensions, no parallel fifths or octaves',
    'romantic':  'Romantic (Schubert/Brahms): rich 7th chords, chromaticism, expressive inner voices',
    'jazz':      'Jazz harmony: 7th and 9th chords, ii-V-I progressions, chromatic voice leading, tritone substitutions',
}

VOICE_RANGES_STR = {
    'soprano': 'C4–G5',
    'alto':    'G3–C5',
    'tenor':   'C3–G4',
    'bass':    'E2–C4',
}

OTHER_VOICES = {
    'soprano': ['alto', 'tenor', 'bass'],
    'alto':    ['soprano', 'tenor', 'bass'],
    'tenor':   ['soprano', 'alto', 'bass'],
    'bass':    ['soprano', 'alto', 'tenor'],
}


def _weirdness_description(w):
    if w <= 20:
        return "extremely conservative — strict traditional voice leading, stay firmly in key, smooth stepwise motion, no surprises"
    elif w <= 40:
        return "moderately traditional — occasional chromatic passing tones, mostly diatonic"
    elif w <= 60:
        return "balanced — mix of conventional and adventurous choices"
    elif w <= 80:
        return "adventurous — frequent chromaticism, unexpected chord substitutions, bold leaps"
    else:
        return "highly experimental — push the boundaries of the era, maximally surprising dissonances and progressions while remaining singable"


def _midi_to_note(midi):
    return music21.pitch.Pitch(midi).nameWithOctave


class ClaudeBackend:
    def harmonize(self, melody, tonic, mode, era, bpm, voice_part='soprano', weirdness=50):
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            print('[ClaudeBackend] ANTHROPIC_API_KEY not set, falling back to rule-based')
            return RuleBasedBackend().harmonize(melody, tonic, mode, era, bpm, voice_part, weirdness)

        try:
            import anthropic
        except ImportError:
            print('[ClaudeBackend] anthropic not installed, falling back to rule-based')
            return RuleBasedBackend().harmonize(melody, tonic, mode, era, bpm, voice_part, weirdness)

        beat_sec = 60.0 / bpm
        era_desc = ERA_DESCRIPTIONS.get(era, ERA_DESCRIPTIONS['classical'])
        voice_part = voice_part.lower()
        other_voices = OTHER_VOICES[voice_part]

        melody_lines = []
        for midi, st, en in melody:
            dur_sec = max(en - st, 0.25)
            ql = max(0.5, round((dur_sec / beat_sec) * 2) / 2)
            melody_lines.append(f'  {_midi_to_note(midi)} ({ql} beats)')

        other_ranges = '\n'.join(
            f'- {v.capitalize()} range: {VOICE_RANGES_STR[v]}'
            for v in other_voices
        )

        prompt = f"""You are an expert choral harmonist. The user has sung/played the {voice_part} voice of a melody. Generate the other three SATB voices to harmonize it.

Key: {tonic} {mode}
Style: {era_desc}
Adventurousness (weirdness={weirdness}/100): {_weirdness_description(weirdness)}

{voice_part.capitalize()} melody (use EXACTLY these pitches and durations):
{chr(10).join(melody_lines)}

Generate the other three voices:
{other_ranges}

Rules:
- The {voice_part} must match the given melody exactly
- Avoid parallel fifths and octaves between any two voices
- Prefer stepwise motion in inner voices
- The weirdness parameter should noticeably affect your harmonic choices
- All voices must stay within their stated ranges

Return ONLY valid JSON, no explanation:
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
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]

        satb = json.loads(raw)

        for voice in ('soprano', 'alto', 'tenor', 'bass'):
            if voice not in satb:
                raise ValueError(f'Claude response missing voice: {voice}')
            if len(satb[voice]) != len(melody):
                raise ValueError(f'{voice} has {len(satb[voice])} notes, expected {len(melody)}')

        return satb
