"""Build the Alliance variants of the toast banners: Textures/toast_<type>_alliance.tga.

The Horde flag is painted into every toast_<type>.tga, left of the frame. This script clears a fixed
area around it (FLAG_AREA, measured once on the originals and shared by all 8 textures, see
tools/preview/alliance_area.png) and puts the scaled-down Alliance flag from tools/assets/alliance_flag.png
there, attached to the frame where the Horde flag is: anchors() measures both flags on every texture and the
run fails when they are apart. Every pixel outside FLAG_AREA stays byte-identical, so the banner geometry in
Pals.lua (STYLE v, PORT_X/PORT_S, MED_X) holds for both factions. Needs Pillow:
python tools/make_alliance_toasts.py
"""
import math
from pathlib import Path
import sys

from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
textures = root / 'KodoTimes' / 'Textures'
source = root / 'tools' / 'assets' / 'alliance_flag.png'
preview_dir = root / 'tools' / 'preview'
TYPES = ['levelup', 'levelround', 'level60', 'death', 'skill', 'craftblue', 'craftepic', 'epicloot']

# Horde flag area in texture pixels (x0, y0, x1, y1; top-left origin, x1/y1 exclusive), union of boxes.
# The frame's outer edge is at x 126; the top-left corner's brace reaches x 117 around y 24-41, and the
# lower corner ornament's left arm x 107 around y 153-171. Nothing of the frame is inside.
FLAG_AREA = [
    (0, 0, 126, 24),      # rod and its shadow, up to the top-left corner post
    (0, 24, 117, 42),     # top of the cloth, left of the corner brace
    (0, 42, 116, 153),    # cloth; its right edge is at x 115 in all 8 textures
    (0, 153, 107, 172),   # tattered end, left of the lower corner ornament
    (0, 172, 117, 192),   # tatter tips and ground shadow below the ornament
]
# kept as it is: the dark backdrop that joins the cloth to the frame (only in some types); the Horde-red
# check covers it together with FLAG_AREA
BACKDROP = (116, 42, 126, 153)
# where the Alliance flag goes, from the Horde flag's anchors on the originals (anchors() checks them on
# every texture): the cloth ends flush with the backdrop at x 116 (exclusive), the cloth's top where it
# wraps over the rod is at row 9 like the Horde cloth's loops, and the cloth's tip is on the last visible row.
# The flag keeps its aspect; the right finial is cut off at the corner post, where the Horde rod ends too.
CLOTH_RIGHT, CLOTH_TOP = 116, 9
CLOTH_ROWS = range(42, 140)     # where both cloths run straight down, above their tattered / pointed ends
FINIAL_CUT = 840                # source column (after cropping) where the right spearhead flares out of the
                                # rod's neck (x 808-836): cut there, the neck runs into the corner post
VISIBLE_H = int(0.6953 * 256)   # smallest STYLE v in Pals.lua: rows below this are never shown
SOURCE_MIN_ALPHA = 8            # source pixels fainter than this are haze around the artwork
TOLERANCE = 3                   # px an Alliance anchor may sit from the Horde one (see anchors())


def horde_red(p):
    """Saturated Horde-banner red; the gold/brown of the Alliance flag and the frame does not count."""
    r, g, b, a = p
    return a >= 32 and r >= 90 and g <= 0.4 * r and b <= 0.4 * r


def area_mask(boxes=FLAG_AREA):
    mask = Image.new('L', (1024, 256), 0)
    draw = ImageDraw.Draw(mask)
    for x0, y0, x1, y1 in boxes:
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=255)
    return mask


def load_flag():
    flag = Image.open(source)
    if flag.mode != 'RGBA' or flag.getchannel('A').getextrema()[0] == 255:
        flag = key_black(flag.convert('RGB'))
    alpha = flag.getchannel('A').point(lambda v: 0 if v < SOURCE_MIN_ALPHA else min(255, v * 255 // 250))
    flag.putalpha(alpha)
    flag = flag.crop(alpha.getbbox())
    flag.paste((0, 0, 0, 0), (FINIAL_CUT, 0, flag.width, flag.height))
    return flag


def key_black(rgb):
    """No usable alpha: make the black backdrop transparent, but only where it touches the border, with a
    soft edge from luminance, so dark cloth and shadows inside the flag stay opaque."""
    lum = rgb.convert('L')
    backdrop = lum.point(lambda v: 255 if v < 40 else 0)
    w, h = rgb.size
    for corner in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        if backdrop.getpixel(corner) == 255:
            ImageDraw.floodfill(backdrop, corner, 128)
    soft = Image.eval(lum, lambda v: min(255, v * 255 // 40))
    alpha = Image.composite(soft, Image.new('L', rgb.size, 255), backdrop.point(lambda v: 255 if v == 128 else 0))
    out = rgb.convert('RGBA')
    out.putalpha(alpha)
    return out


def flag_layer(flag, mask):
    """The Alliance flag on a transparent 1024x256 canvas; transparent pixels next to it get its colour so
    the client's texture filtering does not draw a dark rim around it."""
    alpha = flag.getchannel('A')
    w, h = flag.size
    solid = alpha.point(lambda v: 255 if v >= 128 else 0)
    top = solid.crop((w // 2, 0, w // 2 + 1, h)).getbbox()[1]          # the cloth where it wraps over the rod
    right = alpha.crop((0, h // 4, w, 3 * h // 4)).getbbox()[2]         # the cloth, below the rod
    scale = (VISIBLE_H - CLOTH_TOP) / (h - top)
    x0, y0 = CLOTH_RIGHT - right * scale, CLOTH_TOP - top * scale
    # sub-pixel placement: resample the source region that lands on the canvas left of the corner post,
    # on a transparent margin so the region may reach past the artwork
    cw = mask.getbbox()[2]
    region = (-x0 / scale, -y0 / scale, (cw - x0) / scale, (VISIBLE_H - y0) / scale)
    pad = math.ceil(max(0, -region[0], -region[1], region[2] - w, region[3] - h)) + 1
    padded = Image.new('RGBa', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    padded.paste(flag.convert('RGBa'), (pad, pad))
    small = padded.resize((cw, VISIBLE_H), Image.LANCZOS, box=[v + pad for v in region]).convert('RGBA')
    # resampling ringing around the edges is haze too
    small.putalpha(small.getchannel('A').point(lambda v: 0 if v < SOURCE_MIN_ALPHA else v))
    # the cloth's last column meets the kept backdrop but is soft (the source's edge leans by half a pixel
    # here): make it opaque, so no seam shows through
    sp = small.load()
    for y in CLOTH_ROWS:
        r, g, b, a = sp[CLOTH_RIGHT - 1, y]
        if a:
            sp[CLOTH_RIGHT - 1, y] = (r, g, b, 255)
    layer = Image.new('RGBA', (1024, 256), (0, 0, 0, 0))
    layer.paste(small, (0, 0))
    px, m = layer.load(), mask.load()
    bad = [(x, y) for y in range(256) for x in range(1024) if px[x, y][3] and (not m[x, y] or y >= VISIBLE_H)]
    if bad:
        sys.exit(f'FAIL: the Alliance flag leaves the flag area or the visible height at {bad[:5]}')
    bleed = {}
    for y in range(256):
        for x in range(1024):
            if m[x, y] and not px[x, y][3]:
                near = [px[i, j] for j in range(max(0, y - 2), min(256, y + 3))
                        for i in range(max(0, x - 2), min(1024, x + 3)) if px[i, j][3]]
                if near:
                    wsum = sum(p[3] for p in near)
                    bleed[x, y] = tuple(sum(p[c] * p[3] for p in near) // wsum for c in range(3)) + (0,)
    for xy, p in bleed.items():
        px[xy] = p
    return layer, tuple(round(v) for v in (x0, y0, x0 + w * scale, y0 + h * scale))


def anchors(im, cloth, area):
    """Where a flag meets the frame: the cloth's right edge in rows 42-152, the cloth's top and its lowest
    visible row (both within the cloth's columns), and the rod's top row and right end where it runs into
    the top-left corner post (x 121-125, rows 0-23). Below the rod some Horde textures have a shadow, some
    not, so its bottom is no anchor. cloth(pixel) tells the cloth apart; only pixels in area count."""
    px, m = im.load(), area.load()
    pts = [(x, y) for y in range(VISIBLE_H) for x in range(126) if m[x, y] and cloth(px[x, y])]
    body = [x for x, y in pts if 42 <= y < 153]
    left, right = min(body), max(body)
    hang = [y for x, y in pts if left <= x <= right]
    rod = [(x, y) for y in range(24) for x in range(121, 126) if px[x, y][3] >= 128]
    return {'cloth right': right, 'cloth top': min(hang), 'cloth bottom': max(hang),
            'rod top': min(y for x, y in rod), 'rod end': max(x for x, y in rod)}


def header(path):
    h = path.read_bytes()[:18]
    return {'image type': h[2], 'width': h[12] | h[13] << 8, 'height': h[14] | h[15] << 8,
            'bits per pixel': h[16], 'descriptor': h[17], 'id length': h[0], 'colour map': h[1]}


def main():
    mask = area_mask()
    horde_area = area_mask(FLAG_AREA + [BACKDROP])
    flag = load_flag()
    layer, box = flag_layer(flag, mask)
    print(f'source {source.relative_to(root)}: {flag.width}x{flag.height} after cropping to its alpha')
    print(f'flag area (x0, y0, x1, y1): {FLAG_AREA}; {sum(1 for v in mask.getdata() if v)} px')
    print(f'Alliance flag placed at {box} (cut off at x {mask.getbbox()[2]} and row {VISIBLE_H}),'
          f' visible height {VISIBLE_H} px; kept backdrop {BACKDROP}')
    in_area = [i for i, v in enumerate(horde_area.getdata()) if v]
    ok = True
    outputs = []
    for kind in TYPES:
        src = textures / f'toast_{kind}.tga'
        dst = textures / f'toast_{kind}_alliance.tga'
        orig = Image.open(src)
        orig.load()
        out = orig.copy()
        out.paste(layer, (0, 0), mask)
        out.save(dst, rle=orig.info.get('compression') == 'tga_rle',
                 orientation=orig.info.get('orientation', -1))
        new = Image.open(dst)
        new.load()
        a, b = list(orig.getdata()), list(new.getdata())
        m = list(mask.getdata())
        changed_outside = sum(1 for p, q, k in zip(a, b, m) if not k and p != q)
        red_before = sum(1 for i in in_area if horde_red(a[i]))
        red_after = sum(1 for i in in_area if horde_red(b[i]))
        near = [(x, y) for y in range(192) for x in range(140)
                if not horde_area.getpixel((x, y)) and horde_red(a[y * 1024 + x])]
        h0, h1 = header(src), header(dst)
        same = (new.size == orig.size == (1024, 256) and new.mode == orig.mode
                and new.info.get('compression') == orig.info.get('compression')
                and new.info.get('orientation') == orig.info.get('orientation') and h0 == h1)
        horde = anchors(orig.convert('RGBA'), horde_red, mask)
        alliance = anchors(new.convert('RGBA'), lambda p: p[3] >= 32, mask)
        off = {k: alliance[k] - v for k, v in horde.items() if abs(alliance[k] - v) > TOLERANCE}
        npx = new.convert('RGBA').load()
        seam = sum(1 for y in CLOTH_ROWS if npx[horde['cloth right'], y][3] < 250)
        ok = ok and same and changed_outside == 0 and red_after == 0 and not off and seam == 0
        print(f'{dst.name}: {new.size[0]}x{new.size[1]} mode {new.mode} (orig {orig.mode}),'
              f' compression {new.info.get("compression")} (orig {orig.info.get("compression")}),'
              f' orientation {new.info.get("orientation")} (orig {orig.info.get("orientation")})')
        print(f'  TGA header {h1} {"== original" if h0 == h1 else "!= original " + str(h0)}')
        print(f'  pixels changed outside the flag area: {changed_outside}')
        print(f'  Horde-red pixels in the flag area and the backdrop: {red_before} -> {red_after};'
              f' Horde-red pixels of the original left outside it at x<140, y<192: {len(near)}')
        print(f'  Horde flag anchors    {horde}')
        print(f'  Alliance flag anchors {alliance}')
        print(f'  anchors off by more than {TOLERANCE} px: {off or "none"};'
              f' see-through pixels in the cloth at x {horde["cloth right"]},'
              f' rows {CLOTH_ROWS.start}-{CLOTH_ROWS.stop - 1}: {seam}')
        outputs.append((kind, orig, new))

    # all 8 Alliance banners as the player sees them (about half size), and the flag area on each
    preview_dir.mkdir(exist_ok=True)
    sheet = Image.new('RGBA', (512, 8 * 96), (24, 26, 30, 255))
    debug = Image.new('RGBA', (8 * 288, 192), (255, 0, 255, 255))
    for i, (kind, orig, new) in enumerate(outputs):
        sheet.alpha_composite(new.crop((0, 0, 1024, 184)).resize((512, 92), Image.LANCZOS), (0, i * 96 + 2))
        for j, im in enumerate((orig, new)):
            tile = Image.new('RGBA', (144, 192), (255, 0, 255, 255))
            tile.alpha_composite(im.crop((0, 0, 144, 192)))
            draw = ImageDraw.Draw(tile)
            for x0, y0, x1, y1 in FLAG_AREA:
                draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=(0, 255, 0, 255))
            x0, y0, x1, y1 = BACKDROP
            draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=(0, 255, 255, 255))
            debug.paste(tile, (i * 288 + j * 144, 0))
    sheet.save(preview_dir / 'alliance_toasts.png', optimize=True)
    debug.save(preview_dir / 'alliance_area.png', optimize=True)
    print('wrote tools/preview/alliance_toasts.png and tools/preview/alliance_area.png')
    print('PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
