# [claude-code/claude-sonnet-4-6] rule-based SATB backend — kept as fallback if Claude API unavailable
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


def _best_chord(midi, tonic_midi, chords):
    pc = midi % 12
    for name, tones in chords.items():
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
    def harmonize(self, melody, tonic, mode, era, bpm):
        beat_sec = 60.0 / bpm
        vocab = ERA_TRIADS.get(era, ERA_TRIADS['classical']).get(mode, ERA_TRIADS['classical']['major'])
        tonic_midi = music21.pitch.Pitch(tonic).midi

        satb = {'soprano': [], 'alto': [], 'tenor': [], 'bass': []}
        for midi, st, en in melody:
            dur_sec = max(en - st, 0.25)
            ql = max(0.5, round((dur_sec / beat_sec) * 2) / 2)
            tones = _best_chord(midi, tonic_midi, vocab)

            s = _clamp(midi, 60, 79)
            a = _clamp(tonic_midi + tones[2 % len(tones)], 55, 72)
            t = _clamp(tonic_midi + tones[1 % len(tones)] - 12, 48, 67)
            b = _clamp(tonic_midi + tones[0] - 12, 40, 60)

            satb['soprano'].append({'pitch': _midi_to_pitch(s), 'quarterLength': ql})
            satb['alto'].append(   {'pitch': _midi_to_pitch(a), 'quarterLength': ql})
            satb['tenor'].append(  {'pitch': _midi_to_pitch(t), 'quarterLength': ql})
            satb['bass'].append(   {'pitch': _midi_to_pitch(b), 'quarterLength': ql})

        return satb
