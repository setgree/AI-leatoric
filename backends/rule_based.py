# [claude-code/claude-sonnet-4-6] rule-based SATB backend — local fallback, no API key needed
# Honest label: this produces correct diatonic harmony but no voice leading.
import music21

ERA_TRIADS = {
    'classical': {
        'major': {'I': [0,4,7], 'ii': [2,5,9], 'IV': [5,9,0], 'V': [7,11,2], 'vi': [9,0,4]},
        'minor': {'i': [0,3,7], 'iv': [5,8,0], 'V': [7,11,2], 'VI': [8,0,3], 'VII': [10,2,5]},
    },
    'baroque': {
        'major': {'I': [0,4,7], 'ii': [2,5,9], 'IV': [5,9,0], 'V7': [7,11,2,5], 'vi': [9,0,4]},
        'minor': {'i': [0,3,7], 'iv': [5,8,0], 'V7': [7,11,2,5], 'VI': [8,0,3]},
    },
    'romantic': {
        'major': {'Imaj7': [0,4,7,11], 'ii7': [2,5,9,0], 'IVmaj7': [5,9,0,4], 'V7': [7,11,2,5], 'vi7': [9,0,4,7]},
        'minor': {'im7': [0,3,7,10], 'iv7': [5,8,0,3], 'V7': [7,11,2,5], 'VImaj7': [8,0,3,7], 'VII7': [10,2,5,8]},
    },
    'jazz': {
        'major': {'Imaj7': [0,4,7,11], 'ii7': [2,5,9,0], 'IVmaj7': [5,9,0,4], 'V7': [7,11,2,5], 'vi7': [9,0,4,7], 'bVII7': [10,2,5,8]},
        'minor': {'im7': [0,3,7,10], 'ii7b5': [2,5,8,0], 'iv7': [5,8,0,3], 'V7': [7,11,2,5], 'VImaj7': [8,0,3,7]},
    },
}

# SATB ranges: (lo, hi) in MIDI
VOICE_RANGES = {
    'soprano': (60, 79),
    'alto':    (55, 72),
    'tenor':   (48, 67),
    'bass':    (40, 60),
}


def _best_chord(midi, tonic_midi, chords):
    pc = midi % 12
    for tones in chords.values():
        if pc in [(tonic_midi + t) % 12 for t in tones]:
            return tones
    return next(iter(chords.values()))


def _clamp(m, lo, hi):
    while m < lo: m += 12
    while m > hi: m -= 12
    return m


def _midi_to_pitch(m):
    return music21.pitch.Pitch(m).nameWithOctave


class RuleBasedBackend:
    def harmonize(self, melody, tonic, mode, era, bpm, voice_part='soprano', weirdness=50):
        beat_sec = 60.0 / bpm
        vocab = ERA_TRIADS.get(era, ERA_TRIADS['classical']).get(mode, ERA_TRIADS['classical']['major'])
        tonic_midi = music21.pitch.Pitch(tonic).midi
        voice_part = voice_part.lower()

        # which chord tone index goes to which voice (given the input voice)
        # voices ordered: soprano, alto, tenor, bass
        # tones[0]=root, tones[1]=3rd, tones[2]=5th, tones[3]=7th (if present)
        tone_map = {
            'soprano': {'soprano': None, 'alto': 2, 'tenor': 1, 'bass': 0},
            'alto':    {'soprano': 2,    'alto': None, 'tenor': 1, 'bass': 0},
            'tenor':   {'soprano': 2,    'alto': 1,    'tenor': None, 'bass': 0},
            'bass':    {'soprano': 2,    'alto': 1,    'tenor': 0,    'bass': None},
        }
        assignment = tone_map.get(voice_part, tone_map['soprano'])

        satb = {'soprano': [], 'alto': [], 'tenor': [], 'bass': []}
        for midi, st, en in melody:
            dur_sec = max(en - st, 0.25)
            ql = max(0.5, round((dur_sec / beat_sec) * 2) / 2)
            tones = _best_chord(midi, tonic_midi, vocab)

            notes = {}
            for voice, tone_idx in assignment.items():
                if tone_idx is None:
                    # this is the user's voice — clamp to its range
                    lo, hi = VOICE_RANGES[voice_part]
                    notes[voice] = _clamp(midi, lo, hi)
                else:
                    idx = min(tone_idx, len(tones) - 1)
                    lo, hi = VOICE_RANGES[voice]
                    notes[voice] = _clamp(tonic_midi + tones[idx], lo, hi)

            for voice in ('soprano', 'alto', 'tenor', 'bass'):
                satb[voice].append({'pitch': _midi_to_pitch(notes[voice]), 'quarterLength': ql})

        return satb
