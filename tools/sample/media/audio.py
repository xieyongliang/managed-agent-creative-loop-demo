"""Synthesises short, soft backing tracks for the sample videos. Original tones only; nothing is sampled."""
import sys, wave
import numpy as np

RATE, SECONDS = 44100, 5.2
t = np.arange(int(RATE * SECONDS)) / RATE

def note(freq, start, length, attack=.35, release=.9, level=.2, bright=.25):
    env = np.clip((t - start) / attack, 0, 1) * np.clip((start + length - t) / release, 0, 1)
    env[t < start] = 0
    wobble = 1 + .003 * np.sin(2 * np.pi * 4.5 * t)
    tone = np.sin(2 * np.pi * freq * wobble * t) + bright * np.sin(2 * np.pi * 2 * freq * t) + bright * .4 * np.sin(2 * np.pi * 3 * freq * t)
    return level * env * tone

def pluck(freq, start, level=.16):
    age = np.clip(t - start, 0, None)
    env = np.where(t >= start, np.exp(-age * 3.2) * np.clip(age / .01, 0, 1), 0)
    return level * env * (np.sin(2 * np.pi * freq * t) + .3 * np.sin(2 * np.pi * 2 * freq * t))

def hz(semitones_from_a4):
    return 440 * 2 ** (semitones_from_a4 / 12)

TRACKS = {
    "a": ([-9, -5, -2, 2], [3, 7, 10, 14, 10, 7, 15, 14]),      # C major seventh
    "b": ([-12, -5, -4, 0, 3], [0, 3, 7, 12, 10, 7, 3, 12]),    # A minor ninth
    "c": ([-4, 0, 3, 7], [8, 12, 15, 19, 15, 12, 20, 19]),      # F major seventh
}
for name, (chord, melody) in TRACKS.items():
    left = sum(note(hz(n), 0, SECONDS, level=.11) for n in chord)
    right = sum(note(hz(n) * 1.003, .05, SECONDS - .05, level=.11) for n in chord)
    for i, n in enumerate(melody):
        voice = pluck(hz(n), .45 + i * .55)
        left = left + voice * (.9 if i % 2 else .6)
        right = right + voice * (.6 if i % 2 else .9)
    fade = np.clip((SECONDS - t) / .7, 0, 1) * np.clip(t / .25, 0, 1)
    mix = np.stack([left, right], axis=1) * fade[:, None]
    mix = mix / np.abs(mix).max() * .42
    with wave.open(sys.argv[1] + "/pad-%s.wav" % name, "wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(RATE)
        out.writeframes((mix * 32767).astype("<i2").tobytes())
print("ok")
