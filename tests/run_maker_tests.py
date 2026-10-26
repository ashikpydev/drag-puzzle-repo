"""Tests for the puzzle maker page. Run:  python3 tests/run_maker_tests.py"""
import io
import os
import re
import sys
import zipfile

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
MAKER = 'file://' + os.path.abspath(os.path.join(ROOT, 'extras', 'puzzle-maker', 'puzzle-maker.html'))
PIC = os.path.join(ROOT, 'tools', 'pictures', 'fish.png')
TMP = os.path.join(HERE, '_out_maker')
os.makedirs(TMP, exist_ok=True)
results = []


def check(name, cond, detail=''):
    results.append(bool(cond))
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)[:150]) if detail and not cond else ''))


def drag(pg, frm, to):
    b = pg.query_selector('#cv').bounding_box()
    fx, fy = b['x'] + frm[0] / 100 * b['width'], b['y'] + frm[1] / 100 * b['height']
    tx, ty = b['x'] + to[0] / 100 * b['width'], b['y'] + to[1] / 100 * b['height']
    pg.mouse.move(fx, fy); pg.mouse.down()
    for i in range(1, 11):
        pg.mouse.move(fx + (tx - fx) * i / 10, fy + (ty - fy) * i / 10)
    pg.mouse.up()


def export(pg):
    with pg.expect_download() as dl:
        pg.click('#zip')
    path = os.path.join(TMP, 'out.zip')
    dl.value.save_as(path)
    return zipfile.ZipFile(path)


with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(accept_downloads=True, viewport={'width': 1300, 'height': 1000})
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(MAKER)
    check('zip button disabled before a picture is loaded', pg.query_selector('#zip').is_disabled())

    pg.set_input_files('#file', PIC); pg.wait_for_timeout(400)
    check('name taken from the file name', pg.input_value('#name') == 'fish', pg.input_value('#name'))
    check('zip button enabled after loading a picture', not pg.query_selector('#zip').is_disabled())
    check('3 wrong pieces suggested automatically', len(re.findall(r'Wrong piece', pg.input_value('#rows'))) == 3)
    drag(pg, (51, 46), (54.3, 42.7)); pg.wait_for_timeout(100)
    app = pg.input_value('#appearance')
    m = dict(re.findall(r'(\w+)=([\d.]+)', app))
    check('appearance line has gap and correct=1', 'gap_x' in m and 'gap_y' in m and m.get('correct') == '1' and app.startswith('custom-drag-puzzle('), app)
    check('gap moved to where it was dragged', abs(float(m['gap_x']) - 43.3) < 1.0 and abs(float(m['gap_y']) - 31.7) < 1.0, app)

    z = export(pg)
    names = sorted(z.namelist())
    check('zip is valid (CRC ok)', z.testzip() is None)
    check('zip has scene, 4 pieces and the rows file',
          names == ['fish_form_rows.txt', 'fish_p1.png', 'fish_p2.png', 'fish_p3.png', 'fish_p4.png', 'fish_scene.png'], names)
    orig = Image.open(PIC).convert('RGB')
    scene = Image.open(io.BytesIO(z.read('fish_scene.png'))).convert('RGB')
    p1 = Image.open(io.BytesIO(z.read('fish_p1.png'))).convert('RGB')
    gx, gy = round(float(m['gap_x']) / 100 * 900), round(float(m['gap_y']) / 100 * 900)
    gw = round(float(m['gap_w']) / 100 * 900)
    check('piece 1 is exactly the part of the picture under the gap', ImageChops.difference(p1, orig.crop((gx, gy, gx + gw, gy + gw))).getbbox() is None)
    check('scene gap interior is white', scene.getpixel((gx + gw // 2, gy + gw // 2)) == (255, 255, 255))
    outside = ImageChops.difference(scene.crop((0, 0, 900, gy - 1)), orig.crop((0, 0, 900, gy - 1)))
    check('scene is unchanged outside the gap', outside.getbbox() is None)
    check('all pieces are the same size', len({Image.open(io.BytesIO(z.read(n))).size for n in names if re.search(r'_p\d\.png', n)}) == 1)
    rows = z.read('fish_form_rows.txt').decode()
    check('rows file has the survey row and choice rows incl. 96 and 97',
          'select_one fish' in rows and '\t96\t' in rows and '\t97\t' in rows and 'fish_p4.png' in rows, rows[:200])

    # resize on export
    pg.fill('#maxpx', '300'); pg.dispatch_event('#maxpx', 'input')
    z2 = export(pg)
    s2 = Image.open(io.BytesIO(z2.read('fish_scene.png')))
    check('largest export width is respected', s2.size == (300, 300), s2.size)

    # practice, tries, theme
    pg.check('#prac')
    check('practice sets tries to 9', pg.input_value('#tries') == '9')
    pg.select_option('#theme', 'candy')
    app = pg.input_value('#appearance')
    check('practice and theme appear in the setting', 'practice=1' in app and "theme='candy'" in app, app)
    pg.uncheck('#prac'); pg.fill('#tries', '2'); pg.dispatch_event('#tries', 'input')
    check('tries appears when changed', 'tries=2' in pg.input_value('#appearance'))

    # warnings
    pg.click('#rem'); pg.click('#rem'); pg.click('#rem')
    check('warns when no wrong piece is left', 'at least one wrong piece' in pg.inner_text('#sideWarn') and pg.query_selector('#zip').is_disabled())

    # name sanitising
    pg.fill('#name', 'My Fish 2'); pg.dispatch_event('#name', 'input')
    check('field name is sanitised in the rows', 'my_fish_2' in pg.input_value('#rows'))

    # non-square picture gives square pieces
    wide = Image.new('RGB', (800, 400), (200, 80, 80))
    wide.save(os.path.join(TMP, 'wide pic.png'))
    pg2 = ctx.new_page(); pg2.goto(MAKER)
    pg2.set_input_files('#file', os.path.join(TMP, 'wide pic.png')); pg2.wait_for_timeout(400)
    check('name from "wide pic.png" is clean', pg2.input_value('#name') == 'wide_pic', pg2.input_value('#name'))
    zw = export(pg2)
    sizes = {Image.open(io.BytesIO(zw.read(n))).size for n in zw.namelist() if re.search(r'_p\d\.png', n)}
    check('2:1 picture still gives square pieces', len(sizes) == 1 and list(sizes)[0][0] == list(sizes)[0][1], sizes)
    app = pg2.input_value('#appearance')
    check('2:1 picture: gap_h not needed while square is kept', 'gap_h' not in app, app)
    pg2.uncheck('#square')
    check('gap_h appears when square is switched off', 'gap_h=' in pg2.input_value('#appearance'))

    check('no JavaScript errors', not errs, errs)
    br.close()

print('\n%d checks, %d failed' % (len(results), results.count(False)))
sys.exit(1 if False in results else 0)
