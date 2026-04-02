# [claude-code/claude-sonnet-4-6] unit tests for harmonizer — all use RuleBasedBackend (no API key needed)
import pytest
from music21 import stream, note
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from harmonizer import harmonize_melody, ERA_TRIADS
from backends.rule_based import RuleBasedBackend

RB = RuleBasedBackend()

# a simple 4-note melody in C major: C4 D4 E4 G4
C_MAJOR_MELODY = [
    (60, 0.0, 0.75),
    (62, 0.75, 1.5),
    (64, 1.5, 2.25),
    (67, 2.25, 3.0),
]

A_MINOR_MELODY = [
    (69, 0.0, 0.75),
    (67, 0.75, 1.5),
    (65, 1.5, 2.25),
    (64, 2.25, 3.0),
]


def test_score_has_four_parts():
    score = harmonize_melody(C_MAJOR_MELODY, tonic='C', mode='major', bpm=80, backend=RB)
    assert len(score.parts) == 4


def test_part_ids():
    score = harmonize_melody(C_MAJOR_MELODY, tonic='C', mode='major', bpm=80, backend=RB)
    ids = [p.id for p in score.parts]
    assert ids == ['Soprano', 'Alto', 'Tenor', 'Bass']


def test_note_count_matches_melody():
    score = harmonize_melody(C_MAJOR_MELODY, tonic='C', mode='major', bpm=80, backend=RB)
    for part in score.parts:
        notes = [n for n in part.flatten().notesAndRests if isinstance(n, note.Note)]
        assert len(notes) == len(C_MAJOR_MELODY), f"{part.id} has wrong note count"


def test_soprano_follows_melody():
    score = harmonize_melody(C_MAJOR_MELODY, tonic='C', mode='major', bpm=80, backend=RB)
    soprano_notes = [n for n in score.parts[0].flatten().notesAndRests if isinstance(n, note.Note)]
    for m in [n.pitch.midi for n in soprano_notes]:
        assert 60 <= m <= 79, f"Soprano note {m} out of range"


def test_voice_ranges():
    score = harmonize_melody(C_MAJOR_MELODY, tonic='C', mode='major', bpm=80, backend=RB)
    ranges = {'Soprano': (60, 79), 'Alto': (55, 72), 'Tenor': (48, 67), 'Bass': (40, 60)}
    for part in score.parts:
        lo, hi = ranges[part.id]
        for n in part.flatten().notesAndRests:
            if isinstance(n, note.Note):
                assert lo <= n.pitch.midi <= hi, \
                    f"{part.id} note {n.pitch.midi} outside range [{lo},{hi}]"


def test_all_eras_produce_output():
    for era in ERA_TRIADS:
        score = harmonize_melody(C_MAJOR_MELODY, tonic='C', mode='major', bpm=80, era=era, backend=RB)
        assert len(score.parts) == 4, f"era={era} produced wrong part count"


def test_minor_key():
    score = harmonize_melody(A_MINOR_MELODY, tonic='A', mode='minor', bpm=80, backend=RB)
    assert len(score.parts) == 4
    ks = score.parts[0].flatten().getElementsByClass('KeySignature')
    assert len(list(ks)) > 0


def test_bpm_affects_quarter_lengths():
    score_slow = harmonize_melody(C_MAJOR_MELODY, tonic='C', bpm=60, backend=RB)
    score_fast = harmonize_melody(C_MAJOR_MELODY, tonic='C', bpm=120, backend=RB)
    def total_ql(score):
        return sum(n.quarterLength for n in score.parts[0].flatten().notesAndRests
                   if isinstance(n, note.Note))
    assert total_ql(score_fast) > total_ql(score_slow)


def test_unknown_era_falls_back_gracefully():
    score = harmonize_melody(C_MAJOR_MELODY, tonic='C', era='nonexistent', backend=RB)
    assert len(score.parts) == 4
