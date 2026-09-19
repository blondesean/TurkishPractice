"""Generate the home-screen icons for the web app.

Pure stdlib -- writes PNGs by hand (zlib + struct) so there's no dependency to
install. Draws the crescent and star on Turkish flag red.
Run once; re-run only if you want to change the icon.

    py -3 web/make_icons.py
"""

import math
import os
import struct
import zlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GROUND = (0xE3, 0x0A, 0x17)   # Turkish flag red
WHITE = (0xFF, 0xFF, 0xFF)
SS = 3  # supersampling factor, for smooth edges

SIZES = {"icon-180.png": 180, "icon-192.png": 192, "icon-512.png": 512}


def write_png(path, size, rows):
    raw = b"".join(b"\x00" + bytes(v for px in row for v in px) for row in rows)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)  # 8-bit truecolour
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", header)
                + chunk(b"IDAT", zlib.compress(raw, 9))
                + chunk(b"IEND", b""))


def star_points(cx, cy, outer):
    """Five-pointed star, one point facing right (as on the flag)."""
    pts = []
    inner = outer * 0.382
    for i in range(10):
        angle = math.pi * i / 5 - math.pi / 2
        r = outer if i % 2 == 0 else inner
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return pts


def in_polygon(x, y, pts):
    inside = False
    j = len(pts) - 1
    for i, (xi, yi) in enumerate(pts):
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def render(size):
    """Crescent (a circle minus an offset circle) plus a star, on cobalt."""
    s = size * SS
    # Geometry as fractions of the icon, tuned to sit comfortably inside the
    # rounded mask iOS applies.
    outer_c = (s * 0.44, s * 0.50, s * 0.27)
    inner_c = (s * 0.53, s * 0.50, s * 0.225)
    star = star_points(s * 0.70, s * 0.50, s * 0.115)

    rows = []
    for py in range(size):
        row = []
        for px in range(size):
            hits = 0
            for oy in range(SS):
                for ox in range(SS):
                    x = px * SS + ox + 0.5
                    y = py * SS + oy + 0.5
                    d_out = math.hypot(x - outer_c[0], y - outer_c[1])
                    d_in = math.hypot(x - inner_c[0], y - inner_c[1])
                    if (d_out <= outer_c[2] and d_in > inner_c[2]) or in_polygon(x, y, star):
                        hits += 1
            a = hits / (SS * SS)
            row.append(tuple(round(GROUND[i] + (WHITE[i] - GROUND[i]) * a) for i in range(3)))
        rows.append(row)
    return rows


def main():
    for name, size in SIZES.items():
        path = os.path.join(BASE_DIR, name)
        write_png(path, size, render(size))
        print(f"{name} <- {size}x{size} ({os.path.getsize(path) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
