"""Check the fonts: every bundled .ttf has Hungarian Ő ő Ű ű, and no lua file still uses the game's Morpheus.

The game's Fonts\\MORPHEUS.TTF has no Ő/Ű (the welcome title showed a box), so titles and medallions use the bundled
Marcellus (ns.FONT_TITLE). Standard library only:  python tools/check_fonts.py
"""
from pathlib import Path
import re
import struct
import sys

root = Path(__file__).resolve().parents[1]
FONTS = ['Marcellus-Regular.ttf', 'Barlow-Regular.ttf', 'Barlow-SemiBold.ttf']
NEEDED = {0x0150: 'Ő', 0x0151: 'ő', 0x0170: 'Ű', 0x0171: 'ű'}
failures = []


def cmap_codepoints(data):
    """Every code point mapped to a glyph other than .notdef by the Unicode cmap subtables (formats 4 and 12)."""
    num_tables = struct.unpack_from('>H', data, 4)[0]
    tables = {}
    for i in range(num_tables):
        tag, _, offset, length = struct.unpack_from('>4sIII', data, 12 + 16 * i)
        tables[tag] = (offset, length)
    if b'cmap' not in tables:
        raise ValueError('no cmap table')
    base = tables[b'cmap'][0]
    _, count = struct.unpack_from('>HH', data, base)
    points = set()
    for i in range(count):
        platform, encoding, offset = struct.unpack_from('>HHI', data, base + 4 + 8 * i)
        if not (platform == 0 or (platform == 3 and encoding in (1, 10))):
            continue
        sub = base + offset
        fmt = struct.unpack_from('>H', data, sub)[0]
        if fmt == 4:
            seg2 = struct.unpack_from('>H', data, sub + 6)[0]
            n = seg2 // 2
            ends = struct.unpack_from(f'>{n}H', data, sub + 14)
            starts = struct.unpack_from(f'>{n}H', data, sub + 16 + seg2)
            deltas = struct.unpack_from(f'>{n}h', data, sub + 16 + 2 * seg2)
            range_at = sub + 16 + 3 * seg2
            ranges = struct.unpack_from(f'>{n}H', data, range_at)
            for k in range(n):
                for c in range(starts[k], ends[k] + 1):
                    if c == 0xFFFF:
                        continue
                    if ranges[k] == 0:
                        glyph = (c + deltas[k]) & 0xFFFF
                    else:
                        at = range_at + 2 * k + ranges[k] + 2 * (c - starts[k])
                        glyph = struct.unpack_from('>H', data, at)[0]
                        glyph = (glyph + deltas[k]) & 0xFFFF if glyph else 0
                    if glyph:
                        points.add(c)
        elif fmt == 12:
            groups = struct.unpack_from('>I', data, sub + 12)[0]
            for k in range(groups):
                start, end, glyph = struct.unpack_from('>III', data, sub + 16 + 12 * k)
                points.update(c for j, c in enumerate(range(start, end + 1)) if glyph + j)
    return points


for name in FONTS:
    path = root / 'KodoTimes' / 'Fonts' / name
    try:
        points = cmap_codepoints(path.read_bytes())
    except (OSError, ValueError, struct.error) as err:
        failures.append(f'{name}: cannot read the cmap ({err})')
        continue
    missing = [f'U+{c:04X} {ch}' for c, ch in NEEDED.items() if c not in points]
    if missing:
        failures.append(f'{name} has no glyph for {", ".join(missing)}')
    elif 0x41 not in points:
        failures.append(f'{name}: the cmap parse found no "A", so it cannot be trusted')

for path in sorted(root.glob('KodoTimes/**/*.lua')):
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if re.search('morpheus', line, re.IGNORECASE):
            failures.append(f'{path.relative_to(root).as_posix()}:{number} still uses Morpheus: {line.strip()}')

if failures:
    print('FAIL:')
    for failure in failures:
        print('  ' + failure)
    sys.exit(1)
print(f'PASS: {", ".join(FONTS)} have {" ".join(NEEDED.values())}; no lua file uses Morpheus')
