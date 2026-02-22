from music21 import stream, note, chord, tempo, meter, key
import music21
import numpy as np


def _midi_to_pitchname(midi):
    return music21.pitch.Pitch(midi).nameWithOctave


def harmonize_melody(melody, tonic='C'):
    """Simple rule-based harmonizer assuming C major (or given tonic).

    melody: list of (midi, start_sec, end_sec)
    Returns a music21 Score with four parts (S,A,T,B).
    """
    # create parts
    s_part = stream.Part()
    a_part = stream.Part()
    t_part = stream.Part()
    b_part = stream.Part()

    s_part.id = 'Soprano'
    a_part.id = 'Alto'
    t_part.id = 'Tenor'
    b_part.id = 'Bass'

    # basic meta
    mm = tempo.MetronomeMark(number=100)
    for p in (s_part, a_part, t_part, b_part):
        p.append(mm)
        p.append(meter.TimeSignature('4/4'))
        p.append(key.Key(tonic))

    # diatonic triads in major (root midi offsets from tonic)
    scale_degrees = [0, 2, 4, 5, 7, 9, 11]
    # map to chord tones (triads)
    triads = {
        'I': [0,4,7],
        'ii': [2,5,9],
        'iii': [4,7,11],
        'IV': [5,9,0],
        'V': [7,11,2],
        'vi': [9,0,4],
    }

    # helper: choose a triad where melody pitch class is in chord tones
    def choose_chord(midi):
        pc = midi % 12
        tonic_midi = music21.pitch.Pitch(tonic).midi % 12
        for name, tones in triads.items():
            chord_pcs = [(tonic_midi + t) % 12 for t in tones]
            if pc in chord_pcs:
                return tones
        # fallback to I
        return triads['I']

    for midi, st, en in melody:
        dur = en - st if en > st else 0.5
        chord_tones = choose_chord(midi)
        # map tones to concrete MIDI in ranges for SATB
        tonic_midi = music21.pitch.Pitch(tonic).midi
        # bass: root in lower octave
        bass_midi = tonic_midi + chord_tones[0] - 12
        tenor_midi = tonic_midi + chord_tones[1] - 12
        alto_midi = tonic_midi + chord_tones[2]
        soprano_midi = midi

        s = note.Note(music21.pitch.Pitch(midi).nameWithOctave, quarterLength=dur)
        a = note.Note(music21.pitch.Pitch(music21.pitch.Pitch(alto_midi).midi).nameWithOctave, quarterLength=dur)
        t = note.Note(music21.pitch.Pitch(tenor_midi).nameWithOctave, quarterLength=dur)
        b = note.Note(music21.pitch.Pitch(bass_midi).nameWithOctave, quarterLength=dur)

        s_part.append(s)
        a_part.append(a)
        t_part.append(t)
        b_part.append(b)

    sc = stream.Score()
    sc.append(s_part)
    sc.append(a_part)
    sc.append(t_part)
    sc.append(b_part)
    return sc
