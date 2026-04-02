# [claude-code/claude-sonnet-4-6] integration tests for the /transcribe endpoint
# generates synthetic WAV files (sine waves at known pitches) to test the full pipeline
import pytest
import numpy as np
import io
import struct
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from backend import app

client = TestClient(app)


def make_wav(freqs_and_durations, sample_rate=22050, amplitude=0.5):
    """
    Build a WAV file as bytes.
    freqs_and_durations: list of (hz, seconds) — notes played in sequence.
    Returns bytes of a valid mono 16-bit WAV.
    """
    samples = []
    for hz, dur in freqs_and_durations:
        n = int(sample_rate * dur)
        t = np.linspace(0, dur, n, endpoint=False)
        wave = amplitude * np.sin(2 * np.pi * hz * t)
        samples.append(wave)
    pcm = np.concatenate(samples)
    pcm_int = (pcm * 32767).astype(np.int16)

    buf = io.BytesIO()
    num_samples = len(pcm_int)
    data_size   = num_samples * 2
    buf.write(b'RIFF')
    buf.write(struct.pack('<I', 36 + data_size))
    buf.write(b'WAVE')
    buf.write(b'fmt ')
    buf.write(struct.pack('<IHHIIHH', 16, 1, 1, sample_rate, sample_rate*2, 2, 16))
    buf.write(b'data')
    buf.write(struct.pack('<I', data_size))
    buf.write(pcm_int.tobytes())
    buf.seek(0)
    return buf.read()


# C major scale notes (Hz)
C4  = 261.63
D4  = 293.66
E4  = 329.63
G4  = 392.00
A4  = 440.00


def test_transcribe_returns_200():
    wav = make_wav([(C4, 0.5), (E4, 0.5), (G4, 0.5)])
    resp = client.post(
        '/transcribe',
        data={'bpm': '80', 'era': 'classical', 'voice_part': 'soprano', 'weirdness': '50', 'use_claude': 'false'},
        files={'file': ('test.wav', wav, 'audio/wav')},
    )
    assert resp.status_code == 200, resp.text


def test_response_has_musicxml_key():
    wav = make_wav([(C4, 0.5), (E4, 0.5), (G4, 0.5)])
    resp = client.post(
        '/transcribe',
        data={'bpm': '80', 'era': 'classical', 'voice_part': 'soprano', 'weirdness': '50', 'use_claude': 'false'},
        files={'file': ('test.wav', wav, 'audio/wav')},
    )
    j = resp.json()
    assert 'musicxml' in j
    assert j['musicxml'].endswith('.musicxml')


def test_musicxml_file_exists_on_disk():
    wav = make_wav([(C4, 0.5), (E4, 0.5), (G4, 0.5)])
    resp = client.post(
        '/transcribe',
        data={'bpm': '80', 'era': 'classical', 'voice_part': 'soprano', 'weirdness': '50', 'use_claude': 'false'},
        files={'file': ('test.wav', wav, 'audio/wav')},
    )
    xml_url = resp.json()['musicxml']
    # url is /outputs/musicxml/<uid>.musicxml
    xml_path = xml_url.lstrip('/')
    assert os.path.exists(xml_path), f"MusicXML not found at {xml_path}"


def test_key_is_returned():
    wav = make_wav([(C4, 0.5), (E4, 0.5), (G4, 0.5)])
    resp = client.post(
        '/transcribe',
        data={'bpm': '80', 'era': 'classical', 'voice_part': 'soprano', 'weirdness': '50', 'use_claude': 'false'},
        files={'file': ('test.wav', wav, 'audio/wav')},
    )
    j = resp.json()
    assert 'key' in j
    assert len(j['key']) > 0


def test_all_eras_succeed():
    wav = make_wav([(C4, 0.5), (E4, 0.5), (G4, 0.5)])
    for era in ('classical', 'baroque', 'romantic', 'jazz'):
        resp = client.post(
            '/transcribe',
            data={'bpm': '80', 'era': era, 'voice_part': 'soprano', 'weirdness': '50', 'use_claude': 'false'},
            files={'file': ('test.wav', wav, 'audio/wav')},
        )
        assert resp.status_code == 200, f"era={era} failed: {resp.text}"
        assert 'musicxml' in resp.json()


def test_empty_audio_returns_400():
    """Very short silence should return a 400 with an error message."""
    wav = make_wav([(0.0, 0.1)])   # 100ms of silence
    resp = client.post(
        '/transcribe',
        data={'bpm': '80', 'era': 'classical', 'voice_part': 'soprano', 'weirdness': '50', 'use_claude': 'false'},
        files={'file': ('test.wav', wav, 'audio/wav')},
    )
    assert resp.status_code == 400
    assert 'error' in resp.json()
