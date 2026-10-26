"""Make the preview images used in the README (extras/preview.png and extras/preview.gif)."""
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tests'))
import harness as H
from PIL import Image
from playwright.sync_api import sync_playwright

H.reset_out()
items = H.sample_items()
fish = items['puzzle_1']
EXTRAS = os.path.join(H.ROOT, 'extras')


def grab(pg):
    png = pg.locator('#dp-stage').screenshot()
    return Image.open(io.BytesIO(png)).convert('RGB')


def run(vw, vh, key):
    """Play one puzzle and return (start, drag, win) stills and all frames."""
    ctx = br.new_context(viewport={'width': vw, 'height': vh}, device_scale_factor=1, has_touch=True)
    pg = ctx.new_page()
    pg.goto(H.page_url(key, fish, params={'shuffle': '0'}))
    pg.wait_for_selector('.dp-piece')
    frames = []
    for i in range(6):
        frames.append(grab(pg)); pg.wait_for_timeout(120)
    pg.wait_for_timeout(900)
    start = grab(pg); frames.append(start)
    tx, ty = H.gap_center(pg, fish['params'])
    x, y = H.center(H.piece(pg, '1'))
    pg.mouse.move(x, y); pg.mouse.down()
    drag = None
    for i in range(1, 11):
        pg.mouse.move(x + (tx - x) * i / 10, y + (ty - y) * i / 10)
        frames.append(grab(pg))
        if i == 8:
            drag = frames[-1]
    pg.mouse.up()
    win = None
    for i in range(12):
        pg.wait_for_timeout(60)
        f = grab(pg); frames.append(f)
        if i == 3:
            win = f
    for i in range(3):
        pg.wait_for_timeout(300); frames.append(grab(pg))
    ctx.close()
    return start, drag, win, frames


with sync_playwright() as p:
    br = p.chromium.launch()
    ls, ld, lw, lframes = run(1280, 800, 'prev_land')
    ps, pd, pw_, pframes = run(800, 1280, 'prev_port')
    br.close()

# README still: landscape start / drag / win on one row
w, h = ls.size
row = Image.new('RGB', (w * 3 + 40, h), 'white')
for k, im in enumerate([ls, ld, lw]):
    row.paste(im, (k * (w + 20), 0))
row.thumbnail((1500, 900))
row.save(os.path.join(EXTRAS, 'preview-landscape.png'), optimize=True)

# portrait still
w, h = ps.size
col = Image.new('RGB', (w * 3 + 40, h), 'white')
for k, im in enumerate([ps, pd, pw_]):
    col.paste(im, (k * (w + 20), 0))
col.thumbnail((1500, 900))
col.save(os.path.join(EXTRAS, 'preview-portrait.png'), optimize=True)

# animated gif (landscape tablet), kept small
small = []
for im in lframes:
    s = im.copy(); s.thumbnail((640, 420))
    small.append(s.quantize(colors=128, method=Image.MEDIANCUT))
small[0].save(os.path.join(EXTRAS, 'preview.gif'), save_all=True, append_images=small[1:], duration=110, loop=0, optimize=True)
for f in ('preview-landscape.png', 'preview-portrait.png', 'preview.gif'):
    print(f, os.path.getsize(os.path.join(EXTRAS, f)) // 1024, 'KB')
