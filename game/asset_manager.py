"""
asset_manager.py — Sub Ladder
Handles all asset loading: backgrounds, icons/logos, sounds, music.

Design goals:
  - Never crash the game if an asset is missing (graceful fallback)
  - Auto-generates placeholder assets if the files are absent
  - Provides a clean API to game.py
"""

import os
import sys
import math
import struct
import wave
import threading
import tkinter as tk
from tkinter import PhotoImage

# ── Optional dependencies ──────────────────────────────────────────
try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
    PYGAME_OK = True
except Exception:
    PYGAME_OK = False

# ── Paths ──────────────────────────────────────────────────────────
# Nuitka / PyInstaller detection — see utils.py / main.py comments.
if getattr(sys, "frozen", False):
    _frozen_base = getattr(sys, "_MEIPASS", None) or os.path.dirname(sys.executable)
    GAME_DIR    = os.path.join(_frozen_base, "game")
    BASE_DIR    = os.path.join(_frozen_base, "data")
else:
    GAME_DIR    = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR    = os.path.join(os.path.dirname(GAME_DIR), "data")

PIC_DIR     = os.path.join(BASE_DIR, "pictures")
BG_DIR      = os.path.join(PIC_DIR,  "backgrounds")
LOGO_DIR    = os.path.join(PIC_DIR,  "logos")
FLAG_DIR    = os.path.join(PIC_DIR,  "flags")
SOUND_DIR   = os.path.join(BASE_DIR, "sound")
MUSIC_DIR   = os.path.join(SOUND_DIR,"music")
JINGLE_DIR  = os.path.join(SOUND_DIR,"jingles")

SR = 44100  # sample rate for generated audio

# ══════════════════════════════════════════════════════════════════
# IMAGE GENERATION  (run once if files are missing)
# ══════════════════════════════════════════════════════════════════

def _ensure_dirs():
    for d in [BG_DIR, LOGO_DIR, FLAG_DIR, MUSIC_DIR, JINGLE_DIR]:
        os.makedirs(d, exist_ok=True)


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _make_bg(path, top, bot, accent=None, w=1280, h=720):
    if not PIL_OK:
        return
    import random
    img = Image.new("RGB", (w, h))
    px  = img.load()
    for y in range(h):
        c = _lerp(top, bot, y / h)
        for x in range(w):
            px[x, y] = c
    if accent:
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gd   = ImageDraw.Draw(glow)
        for r in range(300, 0, -10):
            a = max(0, int(25 * (1 - r / 300)))
            gd.ellipse([w//2-r, h//2-r, w//2+r, h//2+r], fill=(*accent, a))
        img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    px = img.load()
    rng = random.Random(7)
    for _ in range(20000):
        x = rng.randint(0, w-1); y = rng.randint(0, h-1)
        c = px[x, y]; d = rng.randint(-5, 5)
        px[x, y] = tuple(max(0, min(255, c[i]+d)) for i in range(3))
    img.save(path)


def _make_flag(path, stripes_v, w=64, h=40):
    """stripes_v: list of RGB for vertical stripes."""
    if not PIL_OK:
        return
    img = Image.new("RGB", (w, h))
    d   = ImageDraw.Draw(img)
    sw  = w // len(stripes_v)
    for i, col in enumerate(stripes_v):
        d.rectangle([i*sw, 0, (i+1)*sw, h], fill=col)
    d.rectangle([0, 0, w-1, h-1], outline=(180,180,180), width=1)
    img.save(path)


def _make_circle_icon(path, text, bg, fg, size=64):
    if not PIL_OK:
        return
    img = Image.new("RGBA", (size, size), (0,0,0,0))
    d   = ImageDraw.Draw(img)
    d.ellipse([2, 2, size-3, size-3], fill=bg)
    try:
        from PIL import ImageFont
        fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size//3)
    except Exception:
        fnt = None
    if fnt:
        bb = d.textbbox((0,0), text, font=fnt)
        tw, th = bb[2]-bb[0], bb[3]-bb[1]
        d.text(((size-tw)//2, (size-th)//2 - 2), text, fill=fg, font=fnt)
    img.save(path)


def ensure_assets():
    """Generate any missing placeholder assets."""
    _ensure_dirs()

    # Backgrounds
    specs = [
        ("menu.png",      (12,18,38),(6,10,22),  (70,110,200)),
        ("bg_q1_5.png",   (18,32,70),(10,22,52), (55,130,175)),
        ("bg_q6_10.png",  (10,16,45),(5,10,30),  (45,65,155)),
        ("bg_q11_15.png", (14,6,20), (4,2,12),   (115,18,38)),
    ]
    for fname, top, bot, acc in specs:
        p = os.path.join(BG_DIR, fname)
        if not os.path.exists(p):
            _make_bg(p, top, bot, acc)

    # Flags
    flag_specs = [
        ("en.png", [(0,36,125),(200,16,46),(0,36,125)]),   # simplified union jack colours
        ("fr.png", [(0,35,149),(255,255,255),(237,41,57)]), # tricolore
    ]
    for fname, stripes in flag_specs:
        p = os.path.join(FLAG_DIR, fname)
        if not os.path.exists(p) and PIL_OK:
            img = Image.new("RGB", (64, 40))
            d   = ImageDraw.Draw(img)
            sw  = 64 // len(stripes)
            for i, col in enumerate(stripes):
                d.rectangle([i*sw, 0, (i+1)*sw, 40], fill=col)
            d.rectangle([0,0,63,39], outline=(180,180,180), width=1)
            img.save(p)

    # Audio — only if pygame available
    if PYGAME_OK:
        _ensure_audio()


# ══════════════════════════════════════════════════════════════════
# AUDIO GENERATION
# ══════════════════════════════════════════════════════════════════

def _tone(freq, duration, volume=0.3, fade=0.04):
    n = int(SR * duration)
    fade_s = int(SR * fade)
    out = []
    for i in range(n):
        t = i / SR
        s = (math.sin(2 * math.pi * freq * t) if freq > 1 else 0.0)
        if i < fade_s:
            s *= i / fade_s
        elif i > n - fade_s:
            s *= (n - i) / fade_s
        out.append(int(s * volume * 32767))
    return out


def _melody(notes):
    out = []
    for freq, dur in notes:
        out += _tone(freq, dur)
    return out


def _write_wav(path, samples):
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def _ensure_audio():
    specs = {
        os.path.join(MUSIC_DIR, "menu.wav"): _melody([
            (261.6,0.4),(329.6,0.4),(392.0,0.4),(523.3,0.6),
            (392.0,0.4),(329.6,0.4),(261.6,0.6),(0.001,0.3),
            (293.7,0.4),(349.2,0.4),(440.0,0.4),(587.3,0.6),
            (440.0,0.4),(349.2,0.4),(293.7,0.8),(0.001,0.4),
        ]),
        os.path.join(MUSIC_DIR, "music_q1_5.wav"): _melody([
            (392.0,0.35),(440.0,0.35),(493.9,0.35),(587.3,0.5),
            (493.9,0.35),(440.0,0.35),(392.0,0.5),(0.001,0.25),
            (349.2,0.35),(392.0,0.35),(440.0,0.35),(523.3,0.5),
            (440.0,0.35),(392.0,0.35),(349.2,0.7),(0.001,0.3),
        ]),
        os.path.join(MUSIC_DIR, "music_q6_10.wav"): _melody([
            (220.0,0.5),(246.9,0.5),(261.6,0.7),(0.001,0.2),
            (293.7,0.5),(261.6,0.5),(246.9,0.7),(0.001,0.2),
            (220.0,0.5),(196.0,0.5),(174.6,0.9),(0.001,0.3),
            (220.0,1.2),(0.001,0.4),
        ]),
        os.path.join(MUSIC_DIR, "music_q11_15.wav"): _melody([
            (146.8,0.2),(155.6,0.2),(164.8,0.2),(174.6,0.3),(0.001,0.1),
            (185.0,0.2),(196.0,0.2),(207.7,0.2),(220.0,0.5),(0.001,0.15),
            (233.1,0.2),(246.9,0.2),(261.6,0.3),(0.001,0.1),
            (246.9,0.2),(233.1,0.2),(220.0,0.3),(207.7,0.2),(196.0,0.5),
            (185.0,0.3),(174.6,0.3),(164.8,0.6),(0.001,0.3),
        ]),
        os.path.join(JINGLE_DIR, "answer_selected.wav"):
            _tone(440,0.12,0.4) + _tone(550,0.08,0.3),
        os.path.join(JINGLE_DIR, "correct.wav"):
            _tone(523.3,0.15,0.4)+_tone(659.3,0.15,0.4)+_tone(783.9,0.5,0.4),
        os.path.join(JINGLE_DIR, "wrong.wav"):
            _tone(349.2,0.2,0.45)+_tone(311.1,0.2,0.45)+_tone(277.2,0.35,0.45),
        os.path.join(JINGLE_DIR, "safe_haven.wav"):
            _melody([(523.3,0.15),(523.3,0.15),(783.9,0.4),(698.5,0.2),(783.9,0.6)]),
        os.path.join(JINGLE_DIR, "win.wav"):
            _melody([(523.3,0.1),(659.3,0.1),(783.9,0.1),(1046.5,0.5),
                     (0.001,0.1),(783.9,0.15),(1046.5,0.8)]),
        os.path.join(JINGLE_DIR, "achievement.wav"):
            _melody([(659.3,0.1),(783.9,0.1),(1046.5,0.3)]),
    }
    for path, samples in specs.items():
        if not os.path.exists(path):
            _write_wav(path, samples)


# ══════════════════════════════════════════════════════════════════
# SOUND ENGINE
# ══════════════════════════════════════════════════════════════════

class SoundEngine:
    """Thin wrapper around pygame.mixer for music + jingles + volume."""

    def __init__(self):
        self._volume   = 0.7   # 0.0–1.0
        self._enabled  = PYGAME_OK
        self._current_music: str | None = None

    # ── Volume ────────────────────────────────────────────────────

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, v: float):
        self._volume = max(0.0, min(1.0, v))
        if self._enabled:
            pygame.mixer.music.set_volume(self._volume)

    # ── Music ─────────────────────────────────────────────────────

    def play_music(self, key: str):
        """key: 'menu' | 'q1_5' | 'q6_10' | 'q11_15'"""
        if not self._enabled:
            return
        path_map = {
            "menu":    os.path.join(MUSIC_DIR, "menu.wav"),
            "q1_5":    os.path.join(MUSIC_DIR, "music_q1_5.wav"),
            "q6_10":   os.path.join(MUSIC_DIR, "music_q6_10.wav"),
            "q11_15":  os.path.join(MUSIC_DIR, "music_q11_15.wav"),
        }
        path = path_map.get(key)
        if not path or not os.path.exists(path):
            return
        if self._current_music == key:
            return  # already playing — don't restart
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self._volume)
            pygame.mixer.music.play(-1)   # -1 = loop forever
            self._current_music = key
        except Exception:
            pass

    def stop_music(self):
        if self._enabled:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        self._current_music = None

    # ── Jingles ───────────────────────────────────────────────────

    def play_jingle(self, key: str):
        """key: 'answer_selected' | 'correct' | 'wrong' | 'safe_haven' | 'win' | 'achievement'"""
        if not self._enabled:
            return
        path = os.path.join(JINGLE_DIR, f"{key}.wav")
        if not os.path.exists(path):
            return
        try:
            sound = pygame.mixer.Sound(path)
            sound.set_volume(self._volume)
            sound.play()
        except Exception:
            pass

    @staticmethod
    def music_key_for_level(level: int) -> str:
        if level <= 5:
            return "q1_5"
        elif level <= 10:
            return "q6_10"
        else:
            return "q11_15"


# ══════════════════════════════════════════════════════════════════
# IMAGE LOADER
# ══════════════════════════════════════════════════════════════════

class ImageLoader:
    """Cache-backed image loader. Returns None gracefully if PIL missing."""

    def __init__(self):
        self._cache: dict[str, ImageTk.PhotoImage] = {}

    def _load(self, path: str, size: tuple | None = None) -> "ImageTk.PhotoImage | None":
        key = f"{path}@{size}"
        if key in self._cache:
            return self._cache[key]
        if not PIL_OK or not os.path.exists(path):
            return None
        try:
            img = Image.open(path).convert("RGBA" if path.endswith(".png") else "RGB")
            if size:
                img = img.resize(size, Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            self._cache[key] = tk_img
            return tk_img
        except Exception:
            return None

    def background(self, key: str, size: tuple | None = None):
        """key: 'menu' | 'q1_5' | 'q6_10' | 'q11_15'"""
        fname = {"menu": "menu.png", "q1_5": "bg_q1_5.png",
                 "q6_10": "bg_q6_10.png", "q11_15": "bg_q11_15.png"}.get(key)
        if not fname:
            return None
        return self._load(os.path.join(BG_DIR, fname), size)

    def flag(self, lang_code: str, size=(32, 20)):
        return self._load(os.path.join(FLAG_DIR, f"{lang_code}.png"), size)

    def logo(self, name: str, size=(32, 32)):
        return self._load(os.path.join(LOGO_DIR, f"{name}.png"), size)

    @staticmethod
    def bg_key_for_level(level: int) -> str:
        if level <= 5:
            return "q1_5"
        elif level <= 10:
            return "q6_10"
        else:
            return "q11_15"
