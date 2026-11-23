#!/usr/bin/env python3
"""Synthesize the ad's 19-second music bed, from scratch, in the build session.

Why generated: a commercial or trending track would risk a copyright mute or a claim on the
posted video, and a muted or removed video scores nothing. Everything here is arithmetic: a
kick, closed hats, a sub bass walking one chord a slide, and a soft pad, all in A minor. Drums
stop when the referral end card comes in, so the card lands in near silence.

No dependency beyond the standard library (numpy is not installed here):

    python3 ad/music.py --out bed.wav
    ffmpeg -i ad.mp4 -i bed.wav -c:v copy -c:a aac -b:a 192k -shortest ad-with-music.mp4
"""

import argparse
import math
import random
import wave
from pathlib import Path

SR = 44100
DUR = 19.0
N = int(SR * DUR)
BPM = 120.0
BEAT = 60.0 / BPM

# One chord a slide, at the slide cuts build_ad.py uses: 3.4, 6.8, 10.4, 13.4, 16.5 s.
CHORDS = [
    (3.4, "Am"),
    (6.8, "F"),
    (10.4, "C"),
    (13.4, "G"),
    (16.5, "Am"),
]
ROOTS = {"Am": 110.00, "F": 87.31, "C": 130.81, "G": 98.00}
TRIADS = {"Am": (0, 3, 7), "F": (0, 4, 7), "C": (0, 4, 7), "G": (0, 4, 7)}

buf = [0.0] * N


def place(start_s: float, sample_at) -> None:
    """Write a voice's samples into the buffer from a start time, clipping at the end."""
    start = int(start_s * SR)
    for i, v in enumerate(sample_at):
        j = start + i
        if j >= N:
            return
        buf[j] += v


def kick(start_s: float, amp: float = 0.85) -> None:
    length = int(0.26 * SR)
    phase = 0.0

    def gen():
        nonlocal phase
        for n in range(length):
            t = n / SR
            f = 45.0 + 95.0 * math.exp(-t * 26.0)
            phase += 2.0 * math.pi * f / SR
            env = math.exp(-t * 16.0)
            click = math.exp(-t * 260.0) * 0.35
            yield (math.sin(phase) * env + click) * amp

    place(start_s, gen())


def hat(start_s: float, amp: float = 0.16, length_s: float = 0.055) -> None:
    rnd = random.Random(int(start_s * 1000))
    length = int(length_s * SR)
    prev = 0.0

    def gen():
        nonlocal prev
        for n in range(length):
            t = n / SR
            x = rnd.uniform(-1.0, 1.0)
            high = x - prev  # a cheap high-pass: the difference of neighbouring noise
            prev = x
            yield high * math.exp(-t * 90.0) * amp

    place(start_s, gen())


def bass(start_s: float, freq: float, dur_s: float, amp: float = 0.34) -> None:
    length = int(dur_s * SR)
    harm = (1.0, 0.42, 0.22, 0.11)

    def gen():
        for n in range(length):
            t = n / SR
            env = min(1.0, t / 0.008) * math.exp(-t * 3.2)
            s = 0.0
            for k, w in enumerate(harm, start=1):
                s += w * math.sin(2.0 * math.pi * freq * k * t)
            yield s * env * amp * 0.5

    place(start_s, gen())


def pad(start_s: float, freq: float, dur_s: float, amp: float = 0.085) -> None:
    length = int(dur_s * SR)

    def gen():
        for n in range(length):
            t = n / SR
            attack = min(1.0, t / 0.35)
            release = min(1.0, max(0.0, (dur_s - t) / 0.4))
            env = attack * release
            s = 0.0
            for k, detune in ((1, 1.0), (2, 1.002), (3, 0.998)):
                s += math.sin(2.0 * math.pi * freq * k * t * detune) / k
            yield s * env * amp

    place(start_s, gen())


def swell(start_s: float, dur_s: float = 0.45, amp: float = 0.07) -> None:
    rnd = random.Random(int(start_s * 977))
    length = int(dur_s * SR)

    def gen():
        for n in range(length):
            t = n / SR
            yield rnd.uniform(-1.0, 1.0) * (t / dur_s) ** 2 * amp

    place(start_s, gen())


def build() -> None:
    # Drums run under the ad only: the end card comes in with nothing but the pad.
    beats = int(16.5 / BEAT)
    for b in range(beats):
        t = b * BEAT
        if b % 2 == 0:
            kick(t)
        hat(t + BEAT / 2)
        if b % 4 == 3:
            hat(t + BEAT * 0.75, amp=0.10, length_s=0.04)

    # A swell into each cut.
    for cut, _ in CHORDS[:-1]:
        swell(cut - 0.45)

    # Bass and pad follow the chord of the slide they sit in, one chord a slide.
    for idx, (start, name) in enumerate(CHORDS):
        end = CHORDS[idx + 1][0] if idx + 1 < len(CHORDS) else DUR
        root = ROOTS[name]
        third, fifth = TRIADS[name][1], TRIADS[name][2]
        steps = int((end - start) / (BEAT / 2))
        for s in range(steps):
            t = start + s * (BEAT / 2)
            freq = root if s % 4 != 3 else root * 2.0 ** (7 / 12)  # a fifth lifts the phrase
            bass(t, freq, BEAT * 0.46 if idx < 4 else BEAT * 1.1, amp=0.30 if idx < 4 else 0.20)
        pad(start, root * 2.0, end - start, amp=0.075 if idx < 4 else 0.10)
        pad(start, root * 2.0 * 2.0 ** (third / 12), end - start, amp=0.055)
        pad(start, root * 2.0 * 2.0 ** (fifth / 12), end - start, amp=0.048)


def write(path: Path) -> None:
    peak = max(abs(v) for v in buf) or 1.0
    gain = 0.89 / peak  # leave the master a decibel of headroom
    fade = int(0.45 * SR)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        frames = bytearray()
        for i, v in enumerate(buf):
            s = v * gain
            if i > N - fade:
                s *= (N - i) / fade
            s = max(-1.0, min(1.0, s))
            pcm = int(s * 32767).to_bytes(2, "little", signed=True)
            frames += pcm + pcm  # mono duplicated: no phase tricks, plays the same everywhere
        w.writeframes(bytes(frames))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="bed.wav")
    a = ap.parse_args()
    build()
    write(Path(a.out))
    print(f"wrote {a.out} ({Path(a.out).stat().st_size} bytes, {DUR:.1f} s, {BPM:.0f} bpm)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
