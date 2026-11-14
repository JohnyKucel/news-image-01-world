#!/usr/bin/env python3
"""news-image-01 entry: one newspaper front page that sums up the world
news of Friday 13 November 2026 in a single image.

Pure Python 3.13 standard library only. No external images, no network,
no randomness -- every run produces the exact same PNG bytes.

Layout (1024x1024, newsprint front page):
  masthead "THE WORLD -- FRIDAY, 13 NOVEMBER 2026"
  hero: FAA lifts the nationwide ground stop after a 4-hour halt
        (control tower, grounded planes, sunrise)
  six story panels, each with a pictogram and a headline:
    UKRAINE   -- 1,200 drones in the biggest raid of the war
    MICROSOFT -- 365 outage enters its second day
    TAIWAN    -- China runs large unannounced Pacific drills
    OIL       -- IEA forecasts a Q4 surplus of 1.7M barrels a day
    NVIDIA    -- CEO Huang resigns; chip-control clash in Washington
    (hero counts as the FAA story; the grid carries five more plus
     a "markets" panel for the tariff threat on Mexican goods)
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024


def rgb(r, g, b):
    return (r, g, b)


# ---- palette -----------------------------------------------------------
PAPER = rgb(246, 241, 227)
PAPER_DARK = rgb(232, 224, 200)
NAVY = rgb(20, 38, 74)
NAVY_LIGHT = rgb(38, 62, 110)
GOLD = rgb(212, 164, 32)
GOLD_LIGHT = rgb(240, 203, 96)
RED = rgb(198, 44, 36)
RED_DARK = rgb(150, 28, 22)
TEAL = rgb(14, 122, 110)
TEAL_LIGHT = rgb(126, 199, 186)
SKY_TOP = rgb(143, 197, 228)
SKY_LOW = rgb(226, 243, 250)
SUN = rgb(255, 196, 66)
CLOUD = rgb(255, 255, 255)
CLOUD_SHADE = rgb(205, 226, 240)
INK = rgb(24, 28, 38)
GREY = rgb(110, 116, 128)
WHITE = rgb(255, 255, 255)
GREEN = rgb(74, 154, 66)
AMBER = rgb(232, 138, 20)
STEEL = rgb(90, 104, 128)
STEEL_DARK = rgb(58, 68, 88)


# ---- 5x7 bitmap font ---------------------------------------------------
# Each glyph: 7 rows of 5 pixels, '#' = on.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def wrap_text(s, max_width, scale):
    """Wrap words to lines that fit max_width pixels at the given scale."""
    char_w = 6 * scale
    max_chars = max(1, max_width // char_w)
    lines = []
    for raw in s.split("\n"):
        words = raw.split(" ")
        cur = ""
        for w in words:
            trial = (cur + " " + w).strip()
            if len(trial) <= max_chars:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
    return lines


# ---- canvas ------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def fill_rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = c[0]
                self.buf[i + 1] = c[1]
                self.buf[i + 2] = c[2]

    def hline(self, x0, x1, y, c):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            self.px(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            self.px(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.px(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for y in range(cy - r, cy + r + 1):
            dx = int(math.sqrt(max(0, r * r - (y - cy) ** 2)))
            self.hline(cx - dx, cx + dx, y, c)

    def ring(self, cx, cy, r, t, c):
        for k in range(t):
            rr = r - k
            for a in range(360):
                th = math.radians(a)
                self.px(int(cx + rr * math.cos(th)), int(cy + rr * math.sin(th)), c)

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(cy - ry, cy + ry + 1):
            t = (y - cy) / ry if ry else 0
            dx = int(rx * math.sqrt(max(0.0, 1.0 - t * t)))
            self.hline(cx - dx, cx + dx, y, c)

    def poly(self, pts, c):
        """Filled polygon via scanline fill."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h - 1, max(ys)) + 1):
            nodes = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                    nodes.append(x)
            nodes.sort()
            for k in range(0, len(nodes) - 1, 2):
                self.hline(int(nodes[k]), int(nodes[k + 1]), y, c)

    def rect_outline(self, x, y, w, h, c, t=1):
        for k in range(t):
            self.hline(x + k, x + w - 1 - k, y + k, c)
            self.hline(x + k, x + w - 1 - k, y + h - 1 - k, c)
            self.vline(x + k, y + k, y + h - 1 - k, c)
            self.vline(x + w - 1 - k, y + k, y + h - 1 - k, c)

    def text(self, x, y, s, c, scale=2):
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch, FONT["?"])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, c)
            cx += 6 * scale
        return cx

    def text_center(self, cx, y, s, c, scale=2):
        self.text(cx - text_width(s, scale) // 2, y, s, c, scale)

    def text_block(self, x, y, s, c, scale, max_width, leading=None):
        lines = wrap_text(s, max_width, scale)
        lh = leading if leading is not None else 9 * scale
        for i, ln in enumerate(lines):
            self.text(x, y + i * lh, ln, c, scale)
        return y + len(lines) * lh


# ---- pictograms ---------------------------------------------------------
def draw_cloud(cv, x, y, s, c, shade):
    # s = overall width
    cv.disc(x + int(s * 0.30), y + int(s * 0.28), int(s * 0.22), c)
    cv.disc(x + int(s * 0.55), y + int(s * 0.20), int(s * 0.28), c)
    cv.disc(x + int(s * 0.78), y + int(s * 0.30), int(s * 0.20), c)
    cv.fill_rect(x + int(s * 0.10), y + int(s * 0.28), int(s * 0.82),
                 int(s * 0.28), c)
    cv.fill_rect(x + int(s * 0.10), y + int(s * 0.48), int(s * 0.82),
                 int(s * 0.08), shade)


def draw_plane(cv, x, y, s, body, wing, win):
    # side-view plane, nose to the right; s = fuselage length
    fy = y + int(s * 0.16)
    cv.ellipse(x + s // 2, fy, s // 2, int(s * 0.13), body)
    cv.poly([(x + int(s * 0.42), fy - int(s * 0.05)),
             (x + int(s * 0.58), fy - int(s * 0.30)),
             (x + int(s * 0.68), fy - int(s * 0.30)),
             (x + int(s * 0.60), fy - int(s * 0.05))], wing)
    cv.poly([(x + int(s * 0.78), fy - int(s * 0.05)),
             (x + int(s * 0.86), fy - int(s * 0.24)),
             (x + int(s * 0.92), fy - int(s * 0.24)),
             (x + int(s * 0.90), fy - int(s * 0.02))], wing)
    cv.poly([(x + int(s * 0.86), fy + int(s * 0.10)),
             (x + int(s * 0.98), fy + int(s * 0.02)),
             (x + int(s * 0.99), fy + int(s * 0.10))], wing)
    for k in range(4):
        wx = x + int(s * (0.30 + 0.12 * k))
        cv.fill_rect(wx, fy - int(s * 0.06), int(s * 0.06), int(s * 0.06), win)
    cv.fill_rect(x + int(s * 0.94), fy - int(s * 0.08), int(s * 0.04),
                 int(s * 0.10), win)


def draw_tower(cv, x, y, h, c, glass):
    w = 26
    cv.poly([(x, y + h), (x + 8, y), (x + w - 8, y), (x + w, y + h)], c)
    cv.fill_rect(x - 8, y - 22, w + 16, 22, c)
    cv.fill_rect(x - 4, y - 18, w + 8, 12, glass)
    cv.vline(x + w // 2, y - 40, y - 22, c)
    cv.disc(x + w // 2, y - 42, 3, RED)


def draw_drone(cv, x, y, s, body, dark):
    cv.fill_rect(x + int(s * 0.30), y + int(s * 0.38), int(s * 0.40),
                 int(s * 0.24), body)
    cv.disc(x + int(s * 0.50), y + int(s * 0.50), int(s * 0.07), dark)
    for gx, gy in ((0.12, 0.18), (0.88, 0.18), (0.12, 0.82), (0.88, 0.82)):
        px = x + int(s * gx)
        py = y + int(s * gy)
        cv.hline(px - int(s * 0.16), px + int(s * 0.16), py, dark)
        cv.disc(px, py, int(s * 0.05), dark)
    cv.line(x + int(s * 0.30), y + int(s * 0.42), x + int(s * 0.12),
            y + int(s * 0.18), dark)
    cv.line(x + int(s * 0.70), y + int(s * 0.42), x + int(s * 0.88),
            y + int(s * 0.18), dark)
    cv.line(x + int(s * 0.30), y + int(s * 0.58), x + int(s * 0.12),
            y + int(s * 0.82), dark)
    cv.line(x + int(s * 0.70), y + int(s * 0.58), x + int(s * 0.88),
            y + int(s * 0.82), dark)


def draw_ship(cv, x, y, s, hull, deck):
    cv.poly([(x, y + int(s * 0.45)), (x + s, y + int(s * 0.45)),
             (x + int(s * 0.88), y + int(s * 0.72)),
             (x + int(s * 0.12), y + int(s * 0.72))], hull)
    cv.fill_rect(x + int(s * 0.38), y + int(s * 0.12), int(s * 0.24),
                 int(s * 0.33), deck)
    cv.fill_rect(x + int(s * 0.30), y + int(s * 0.26), int(s * 0.40),
                 int(s * 0.19), deck)
    cv.vline(x + int(s * 0.50), y, y + int(s * 0.12), deck)
    cv.poly([(x + int(s * 0.50), y), (x + int(s * 0.72), y + int(s * 0.07)),
             (x + int(s * 0.50), y + int(s * 0.14))], RED)
    for k in range(3):
        wx = x + int(s * (0.28 + 0.18 * k))
        cv.fill_rect(wx, y + int(s * 0.52), int(s * 0.08), int(s * 0.08),
                     PAPER)


def draw_barrel(cv, x, y, w, h, c, band):
    cv.fill_rect(x, y, w, h, c)
    cv.fill_rect(x, y + int(h * 0.18), w, 5, band)
    cv.fill_rect(x, y + int(h * 0.72), w, 5, band)
    cv.ellipse(x + w // 2, y, w // 2, 6, band)
    cv.ellipse(x + w // 2, y + h, w // 2, 6, band)


def draw_chip(cv, x, y, s, body, pin):
    cv.fill_rect(x, y, s, s, body)
    cv.fill_rect(x + int(s * 0.22), y + int(s * 0.22), int(s * 0.56),
                 int(s * 0.56), NAVY)
    for k in range(4):
        off = int(s * (0.18 + 0.22 * k))
        cv.fill_rect(x + off, y - 10, 8, 10, pin)
        cv.fill_rect(x + off, y + s, 8, 10, pin)
        cv.fill_rect(x - 10, y + off, 10, 8, pin)
        cv.fill_rect(x + s, y + off, 10, 8, pin)


def draw_bolt(cv, x, y, s, c):
    cv.poly([(x + int(s * 0.55), y), (x + int(s * 0.20), y + int(s * 0.55)),
             (x + int(s * 0.45), y + int(s * 0.55)),
             (x + int(s * 0.35), y + s),
             (x + int(s * 0.80), y + int(s * 0.45)),
             (x + int(s * 0.55), y + int(s * 0.45))], c)


# ---- page --------------------------------------------------------------
def render():
    cv = Canvas(W, H, PAPER)
    # outer border
    cv.rect_outline(8, 8, W - 16, H - 16, NAVY, 4)
    cv.rect_outline(16, 16, W - 32, H - 32, GOLD, 2)

    # ---- masthead ------------------------------------------------------
    cv.fill_rect(24, 24, W - 48, 94, NAVY)
    cv.text_center(512, 36, "THE WORLD", WHITE, 7)
    cv.fill_rect(64, 92, 896, 3, GOLD)
    cv.text_center(512, 98, "FRIDAY  -  13 NOVEMBER 2026", GOLD_LIGHT, 2)
    cv.text(48, 98, "WORLD NEWS", GOLD_LIGHT, 2)
    cv.text(1024 - 48 - text_width("ONE PAGE, SIX STORIES", 2), 98,
             "ONE PAGE, SIX STORIES", GOLD_LIGHT, 2)

    # ---- hero: FAA ------------------------------------------------------
    hx, hy, hw, hh = 24, 130, 976, 348
    cv.fill_rect(hx, hy, hw, hh, SKY_LOW)
    # sky bands
    for i in range(6):
        yy = hy + i * 30
        cv.fill_rect(hx, yy, hw, 30, SKY_TOP if i < 2 else SKY_LOW)
    # sun + clouds (kept clear of the hero text card on the right)
    cv.disc(560, 178, 30, SUN)
    cv.ring(560, 178, 40, 3, GOLD_LIGHT)
    draw_cloud(cv, 330, 150, 100, CLOUD, CLOUD_SHADE)
    draw_cloud(cv, 120, 170, 90, CLOUD, CLOUD_SHADE)
    # runway + grass
    cv.fill_rect(hx, hy + 268, hw, 80, GREEN)
    cv.fill_rect(hx, hy + 300, hw, 10, WHITE)
    for k in range(9):
        cv.fill_rect(hx + 40 + k * 104, hy + 318, 52, 6, GOLD)
    cv.fill_rect(hx, hy + 330, hw, 18, STEEL_DARK)
    # tower
    draw_tower(cv, 70, hy + 150, 118, STEEL, GOLD_LIGHT)
    # parked planes
    draw_plane(cv, 180, hy + 232, 170, WHITE, STEEL, NAVY_LIGHT)
    draw_plane(cv, 430, hy + 246, 130, RED, STEEL_DARK, WHITE)
    # hero text card (right)
    tx, ty, tw, th = 640, 146, 336, 316
    cv.fill_rect(tx, ty, tw, th, WHITE)
    cv.rect_outline(tx, ty, tw, th, NAVY, 3)
    cv.fill_rect(tx, ty, tw, 34, RED)
    cv.text_center(tx + tw // 2, ty + 9, "TOP STORY", WHITE, 2)
    cv.text_block(tx + 18, ty + 52, "FLIGHTS RESUME AFTER 4-HOUR HALT",
                  NAVY, 4, tw - 36, leading=34)
    cv.text_block(tx + 18, ty + 196,
                  "FAA lifts its nationwide ground stop on Friday evening.",
                  INK, 2, tw - 36, leading=18)
    cv.text_block(tx + 18, ty + 250,
                  "Departures halted by a communications failure. Delays linger.",
                  GREY, 2, tw - 36, leading=18)

    # ---- story grid -----------------------------------------------------
    # (tag, tag colour, headline, body, pictogram key)
    stories = [
        ("UKRAINE", RED, "1,200 DRONES IN BIGGEST RAID",
         "Kyiv strikes deep as peace talks widen.",
         "drone"),
        ("MICROSOFT 365", TEAL, "OUTAGE ENTERS DAY TWO",
         "Outlook, Teams, Copilot still down.",
         "cloud"),
        ("TAIWAN", NAVY_LIGHT, "CHINA'S BIG PACIFIC DRILLS",
         "Taipei calls it intimidation.",
         "ship"),
        ("OIL", AMBER, "IEA SEES OIL SURPLUS",
         "Supply tops demand by 1.7M a day.",
         "barrel"),
        ("NVIDIA", STEEL_DARK, "HUANG RESIGNS AT NVIDIA",
         "Chip clash splits Washington.",
         "chip"),
        ("TRADE", GREEN, "TARIFF THREAT ON MEXICO",
         "US warns tariffs will double.",
         "bolt"),
    ]
    gx, gy = 24, 492
    cw, ch = 320, 236
    gap = 8
    for idx, (tag, tcol, head, body, pic) in enumerate(stories):
        col = idx % 3
        row = idx // 3
        x = gx + col * (cw + gap)
        y = gy + row * (ch + gap)
        cv.fill_rect(x, y, cw, ch, WHITE)
        cv.rect_outline(x, y, cw, ch, NAVY, 2)
        cv.fill_rect(x, y, cw, 10, tcol)
        cv.text(x + 12, y + 20, tag, tcol, 2)
        # pictogram strip
        py = y + 44
        if pic == "drone":
            cv.fill_rect(x, py, cw, 84, rgb(235, 238, 244))
            draw_drone(cv, x + 118, py + 4, 76, STEEL_DARK, NAVY)
        elif pic == "cloud":
            cv.fill_rect(x, py, cw, 84, rgb(226, 240, 246))
            draw_cloud(cv, x + 96, py + 8, 130, WHITE, CLOUD_SHADE)
            draw_bolt(cv, x + 216, py + 30, 34, GOLD)
            cv.text(x + 22, py + 56, "365", TEAL, 2)
        elif pic == "ship":
            cv.fill_rect(x, py, cw, 84, rgb(214, 232, 244))
            for k in range(3):
                cv.fill_rect(x + 20 + k * 96, py + 62, 64, 5, TEAL_LIGHT)
            draw_ship(cv, x + 88, py + 6, 140, STEEL_DARK, NAVY_LIGHT)
        elif pic == "barrel":
            cv.fill_rect(x, py, cw, 84, rgb(246, 238, 214))
            draw_barrel(cv, x + 96, py + 8, 52, 68, AMBER, RED_DARK)
            draw_barrel(cv, x + 164, py + 20, 44, 56, STEEL, STEEL_DARK)
            cv.text(x + 226, py + 30, "$", NAVY, 3)
        elif pic == "chip":
            cv.fill_rect(x, py, cw, 84, rgb(232, 234, 240))
            draw_chip(cv, x + 128, py + 6, 64, STEEL_DARK, GOLD)
            cv.text(x + 148, py + 30, "AI", WHITE, 2)
        else:  # bolt / trade
            cv.fill_rect(x, py, cw, 84, rgb(230, 242, 228))
            draw_bolt(cv, x + 140, py + 8, 52, GOLD)
            cv.text(x + 34, py + 30, "2X", RED, 3)
            cv.text(x + 232, py + 30, "%", NAVY, 3)
        # headline + body
        cv.text_block(x + 12, y + 140, head, NAVY, 3, cw - 24, leading=26)
        cv.text_block(x + 12, y + 196, body, GREY, 2, cw - 24, leading=18)

    # ---- footer ---------------------------------------------------------
    cv.fill_rect(24, 984, 976, 24, NAVY)
    cv.text_center(512, 990,
                   "SIX STORIES THAT SHAPED FRIDAY, 13 NOVEMBER 2026",
                   GOLD_LIGHT, 2)
    return cv.buf


def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(rgb_bytes, w, h):
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)  # filter: none
        raw += rgb_bytes[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    return png


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    png = encode_png(render(), W, H)
    path = os.path.join(out_dir, "entry.png")
    # Write atomically via a temp file in the same directory, so an
    # interrupted run can never leave a partial entry.png behind.
    tmp_path = path + ".tmp"
    with open(tmp_path, "wb") as f:
        f.write(png)
    os.replace(tmp_path, path)
    print(f"wrote {path} ({len(png)} bytes)")


if __name__ == "__main__":
    main()
