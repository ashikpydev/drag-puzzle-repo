"""Browser tests for the drag puzzle plug-in. Run:  python3 tests/run_tests.py
Needs: pip install playwright openpyxl pillow  and  playwright install chromium
"""
import os
import sys

from playwright.sync_api import sync_playwright

import harness as H

results = []


def check(name, cond, detail=''):
    results.append(bool(cond))
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)[:150]) if detail and not cond else ''))


H.reset_out()
items = H.sample_items()
practice, fish, house = items['puzzle_practice'], items['puzzle_1'], items['puzzle_2']

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 800, 'height': 1100}, has_touch=True)
    pg = ctx.new_page()
    errors = []
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)

    def open_item(key, item, **kw):
        pg.goto(H.page_url(key, item, **kw))
        pg.wait_for_selector('.dp-piece')
        pg.wait_for_timeout(1100)   # let the entrance animation finish

    # ---------- 1. Setup read from the form ----------
    open_item('fish1', fish, params={'shuffle': '0'})
    check('4 pieces shown, special codes 96/97 hidden', len(pg.query_selector_all('.dp-piece')) == 4)
    check('no setup problem', pg.query_selector('#dp-problem').is_hidden())
    check('question label shown', 'missing piece' in pg.inner_text('.label'))
    check('theme class default sky', 'dp-theme-sky' in pg.get_attribute('#dp-root', 'class'))
    check('answer empty until the child acts', pg.evaluate('window.__answer') == '')
    pg.screenshot(path=os.path.join(H.OUT, 'shot_start.png'))

    # ---------- 2. Wrong first drop is stored as that choice ----------
    tx, ty = H.gap_center(pg, fish['params'])
    H.drag_to(pg, H.piece(pg, '3'), tx, ty)
    check('wrong drop stores the wrong choice value', pg.evaluate('window.__answer') == '3', pg.evaluate('window.__answer'))
    meta = pg.evaluate('window.__meta')
    check('log says incorrect, 1 attempt', 'status=incorrect' in meta and 'attempts=1' in meta and 'answer=3' in meta, meta)
    check('tries=1: item ends and pieces lock', pg.query_selector('.dp-piece.dp-locked') is not None)
    pg.click('#dp-gear')
    check('special buttons disabled after an answer', pg.query_selector('#dp-cannot').is_disabled())
    pg.screenshot(path=os.path.join(H.OUT, 'shot_wrong.png'))

    # ---------- 3. Correct drop stored, snapped, celebrated ----------
    open_item('fish2', fish, params={'shuffle': '0'})
    tx, ty = H.gap_center(pg, fish['params'])
    sc = pg.query_selector('#dp-scene').bounding_box()
    H.drag_to(pg, H.piece(pg, '1'), tx, ty, wait=350)
    check('correct drop stores value 1', pg.evaluate('window.__answer') == '1', pg.evaluate('window.__answer'))
    meta = pg.evaluate('window.__meta')
    check('log says correct, 1 attempt, order logged', 'status=correct' in meta and 'attempts=1' in meta and 'order=1,2,3,4' in meta, meta)
    pb = pg.query_selector('.dp-piece.dp-placed').bounding_box()
    gx = sc['x'] + float(fish['params']['gap_x']) / 100 * sc['width']
    gy = sc['y'] + float(fish['params']['gap_y']) / 100 * sc['height']
    check('piece snapped exactly into the gap', abs(pb['x'] - gx) < 1.5 and abs(pb['y'] - gy) < 1.5, (pb, gx, gy))
    check('scene bounce class added', 'dp-win' in pg.get_attribute('#dp-scene', 'class'))
    check('star reward shown', pg.query_selector('.dp-star') is not None)
    check('confetti particles created', len(pg.query_selector_all('.dp-confetti')) >= 10, len(pg.query_selector_all('.dp-confetti')))
    pg.screenshot(path=os.path.join(H.OUT, 'shot_win.png'))
    pg.wait_for_timeout(1800)
    check('other pieces fade out after the win', len(pg.query_selector_all('.dp-piece.dp-fade')) == 3)

    # ---------- 4. Dropping outside the gap is not an attempt ----------
    open_item('fish3', fish, params={'shuffle': '0'})
    sc = pg.query_selector('#dp-scene').bounding_box()
    H.drag_to(pg, H.piece(pg, '2'), sc['x'] + 30, sc['y'] + 30)
    check('drop outside gap: no answer', pg.evaluate('window.__answer') == '')
    tx, ty = H.gap_center(pg, fish['params'])
    H.drag_to(pg, H.piece(pg, '1'), tx, ty)
    meta = pg.evaluate('window.__meta')
    check('moves counted separately from attempts', 'moves=2' in meta and 'attempts=1' in meta, meta)

    # ---------- 5. Glow when a piece is near the gap ----------
    open_item('fish4', fish, params={'shuffle': '0'})
    tx, ty = H.gap_center(pg, fish['params'])
    x, y = H.center(H.piece(pg, '2'))
    pg.mouse.move(x, y); pg.mouse.down(); pg.mouse.move(tx, ty, steps=8)
    check('gap glows when a piece is near', 'dp-near' in pg.get_attribute('.dp-gap', 'class'))
    check('lifted piece class while dragging', 'dp-drag' in H.piece(pg, '2').get_attribute('class'))
    pg.screenshot(path=os.path.join(H.OUT, 'shot_drag.png'))
    pg.mouse.up(); pg.wait_for_timeout(300)

    # ---------- 6. Several tries, record first vs last ----------
    open_item('multi_first', fish, params={'shuffle': '0', 'tries': 3})
    tx, ty = H.gap_center(pg, fish['params'])
    H.drag_to(pg, H.piece(pg, '3'), tx, ty)
    check('tries=3: wrong drop does not end the item', pg.query_selector('.dp-piece.dp-locked') is None)
    H.drag_to(pg, H.piece(pg, '1'), tx, ty)
    check('record=first keeps the first (wrong) answer', pg.evaluate('window.__answer') == '3', pg.evaluate('window.__answer'))
    meta = pg.evaluate('window.__meta')
    check('log still shows the child got it right', 'status=correct' in meta and 'attempts=2' in meta and 'seq=3,1' in meta, meta)
    open_item('multi_last', fish, params={'shuffle': '0', 'tries': 3, 'record': 'last'})
    tx, ty = H.gap_center(pg, fish['params'])
    H.drag_to(pg, H.piece(pg, '3'), tx, ty)
    H.drag_to(pg, H.piece(pg, '1'), tx, ty)
    check("record='last' stores the final answer", pg.evaluate('window.__answer') == '1', pg.evaluate('window.__answer'))
    open_item('maxtries', fish, params={'shuffle': '0', 'tries': 2})
    tx, ty = H.gap_center(pg, fish['params'])
    H.drag_to(pg, H.piece(pg, '3'), tx, ty); H.drag_to(pg, H.piece(pg, '2'), tx, ty)
    check('item ends when tries are used up', 'status=incorrect' in pg.evaluate('window.__meta') and pg.query_selector('.dp-piece.dp-locked') is not None)
    check('no reveal by default', pg.query_selector('.dp-piece.dp-right') is None)

    # ---------- 7. Practice item ----------
    open_item('practice', practice, params={'shuffle': '0'})
    check('practice shows 3 pieces', len(pg.query_selector_all('.dp-piece')) == 3)
    check('practice theme applied', 'dp-theme-sunny' in pg.get_attribute('#dp-root', 'class'))
    pg.wait_for_timeout(1200)
    check('demo hand appears for practice', pg.query_selector('.dp-hand') is not None)
    pg.screenshot(path=os.path.join(H.OUT, 'shot_demo.png'))
    tx, ty = H.gap_center(pg, practice['params'])
    H.drag_to(pg, H.piece(pg, '2'), tx, ty)
    check('demo hand removed when the child touches', pg.query_selector('.dp-hand') is None)
    check('practice allows more tries', pg.query_selector('.dp-piece.dp-locked') is None)
    H.drag_to(pg, H.piece(pg, '1'), tx, ty)
    check('practice finishes on the right piece', 'status=correct' in pg.evaluate('window.__meta'))
    pg.click('#dp-gear')
    check('restart visible for practice', pg.query_selector('#dp-restart').is_visible())
    pg.click('#dp-restart')
    check('restart clears answer and log', pg.evaluate('window.__answer') == '' and pg.evaluate('window.__meta') == '')
    check('restart makes pieces draggable again', pg.query_selector('.dp-piece.dp-locked') is None)
    open_item('practice_reveal', practice, params={'shuffle': '0', 'tries': 1})
    tx, ty = H.gap_center(pg, practice['params'])
    H.drag_to(pg, H.piece(pg, '2'), tx, ty)
    check('practice reveals the right piece when tries run out', pg.query_selector('.dp-piece.dp-right') is not None)

    # ---------- 8. Special codes ----------
    open_item('special', fish)
    pg.click('#dp-gear'); pg.click('#dp-cannot')
    check('"could not do it" saves 96', pg.evaluate('window.__answer') == '96')
    check('log marks special', 'status=special' in pg.evaluate('window.__meta'))
    check('pieces locked after special code', pg.query_selector('.dp-piece.dp-locked') is not None)
    open_item('special2', fish)
    pg.click('#dp-gear'); pg.click('#dp-refuse')
    check('"refused" saves 97', pg.evaluate('window.__answer') == '97')
    only_pieces = [c for c in fish['choices'] if c['value'] not in ('96', '97')]
    open_item('special3', fish, params={'code_cannot': '-91', 'code_refuse': '-92'},
              choices=only_pieces + [{'value': '-91', 'label': 'x', 'image': ''}, {'value': '-92', 'label': 'y', 'image': ''}])
    check('custom code values are hidden from pieces and cause no banner',
          len(pg.query_selector_all('.dp-piece')) == 4 and pg.query_selector('#dp-problem').is_hidden(), len(pg.query_selector_all('.dp-piece')))
    pg.click('#dp-gear'); pg.click('#dp-cannot')
    check('custom code value is saved', pg.evaluate('window.__answer') == '-91', pg.evaluate('window.__answer'))

    # ---------- 9. Revisiting a saved answer ----------
    open_item('rev1', fish, params={'shuffle': '0'}, current='1', meta='v=1;status=correct;answer=1;correct=1;attempts=1;seq=1;moves=1')
    check('revisit (right answer): piece placed in gap', pg.query_selector('.dp-piece.dp-placed.dp-right') is not None)
    check('revisit: pieces locked', pg.query_selector('.dp-piece.dp-locked') is not None)
    open_item('rev2', fish, params={'shuffle': '0'}, current='3')
    check('revisit (wrong answer): chosen piece placed, not marked right', pg.query_selector('.dp-piece.dp-placed') is not None and pg.query_selector('.dp-piece.dp-right') is None)
    open_item('rev3', fish, current='97')
    check('revisit (special code): locked', pg.query_selector('.dp-piece.dp-locked') is not None)

    # ---------- 10. clearAnswer ----------
    open_item('clear', fish, params={'shuffle': '0'})
    tx, ty = H.gap_center(pg, fish['params'])
    H.drag_to(pg, H.piece(pg, '1'), tx, ty)
    pg.evaluate('window.clearAnswer()')
    pg.wait_for_timeout(300)
    check('clearAnswer resets the game and the answer', pg.evaluate('window.__answer') == '' and pg.query_selector('.dp-piece.dp-locked') is None)

    # ---------- 11. Read only ----------
    open_item('ro', fish, params={'shuffle': '0'}, readonly=True)
    tx, ty = H.gap_center(pg, fish['params'])
    H.drag_to(pg, H.piece(pg, '1'), tx, ty)
    check('read-only: dragging does nothing', pg.evaluate('window.__answer') == '')

    # ---------- 12. Setup problems are visible ----------
    pg.goto(H.page_url('bad1', fish, scene='no_such_picture.png')); pg.wait_for_timeout(800)
    check('missing scene picture shows a banner', 'no_such_picture.png' in pg.inner_text('#dp-problem'))
    bad = [dict(c) for c in fish['choices']]; bad[1]['image'] = ''
    pg.goto(H.page_url('bad2', fish, choices=bad)); pg.wait_for_timeout(800)
    check('choice without image shows a banner', 'has no image' in pg.inner_text('#dp-problem'))
    bad = [dict(c) for c in fish['choices']]; bad[2]['image'] = 'nope.png'
    pg.goto(H.page_url('bad3', fish, choices=bad)); pg.wait_for_timeout(800)
    check('missing piece picture shows a banner', 'nope.png' in pg.inner_text('#dp-problem'))
    pg.goto(H.page_url('bad4', fish, params={'gap_x': None, 'gap_y': None})); pg.wait_for_timeout(800)
    check('missing gap position shows a banner', 'gap_x' in pg.inner_text('#dp-problem'))
    pg.goto(H.page_url('bad5', fish, params={'correct': '9'})); pg.wait_for_timeout(800)
    check('wrong correct= value shows a banner', 'correct=9' in pg.inner_text('#dp-problem'))
    pg.goto(H.page_url('bad6', fish, params={'theme': 'purple'})); pg.wait_for_timeout(800)
    check('unknown theme shows a banner and falls back', 'theme' in pg.inner_text('#dp-problem') and 'dp-theme-sky' in pg.get_attribute('#dp-root', 'class'))
    pg.goto(H.page_url('def_correct', fish, params={'correct': None, 'shuffle': '0'})); pg.wait_for_selector('.dp-piece'); pg.wait_for_timeout(1000)
    tx, ty = H.gap_center(pg, fish['params'])
    H.drag_to(pg, H.piece(pg, '1'), tx, ty)
    check('correct defaults to the choice with value 1', 'status=correct' in pg.evaluate('window.__meta'))

    # ---------- 13. Audio prompt ----------
    pg.goto(H.page_url('audio', fish, audio='prompt.mp3')); pg.wait_for_selector('.dp-piece')
    check('speaker button shown when the question has audio', pg.query_selector('#dp-speaker').is_visible())
    pg.goto(H.page_url('noaudio', fish)); pg.wait_for_selector('.dp-piece')
    check('speaker button hidden without audio', pg.query_selector('#dp-speaker').is_hidden())

    # ---------- 14. Layouts ----------
    pg.set_viewport_size({'width': 360, 'height': 800})
    open_item('phone', fish, params={'shuffle': '0'})
    st = pg.query_selector('#dp-stage').bounding_box()
    pcs = [e.bounding_box() for e in pg.query_selector_all('.dp-piece')]
    g = pg.query_selector('#dp-game').bounding_box()
    check('phone width: stage fits the screen', st['x'] >= 0 and st['x'] + st['width'] <= 361, st)
    check('phone width: pieces inside the game box', all(q['x'] >= g['x'] - 1 and q['x'] + q['width'] <= g['x'] + g['width'] + 1 for q in pcs))
    tx, ty = H.gap_center(pg, fish['params'])
    H.drag_to(pg, H.piece(pg, '1'), tx, ty)
    check('phone width: drag works', 'status=correct' in pg.evaluate('window.__meta'))
    pg.set_viewport_size({'width': 800, 'height': 1100})
    pg.set_viewport_size({'width': 800, 'height': 1100})
    open_item('onerow', fish, params={'shuffle': '0'})
    ys = {round(e.bounding_box()['y']) for e in pg.query_selector_all('.dp-piece')}
    check('4 pieces fit on one row on a tablet', len(ys) == 1, ys)
    open_item('gapoff', fish, params={'shuffle': '0'})
    tx, ty = H.gap_center(pg, fish['params'])
    H.drag_to(pg, H.piece(pg, '1'), tx, ty)
    check('gap outline hidden after the right piece lands', 'dp-off' in pg.get_attribute('.dp-gap', 'class'))
    open_item('wide', fish, params={'shuffle': '0', 'gap_w': 40, 'gap_h': 40, 'gap_x': 30, 'gap_y': 30})
    g = pg.query_selector('#dp-game').bounding_box()
    pcs = [e.bounding_box() for e in pg.query_selector_all('.dp-piece')]
    check('big gap: pieces wrap to two rows and stay inside', len({round(q['y']) for q in pcs}) >= 2 and all(q['y'] + q['height'] <= g['y'] + g['height'] + 1 for q in pcs))

    # ---------- 14b. Tablet sizes (most fieldwork is on tablets) ----------
    TABLETS = [('10in landscape 1280x800', 1280, 800, 'side'), ('10in portrait 800x1280', 800, 1280, 'stacked'),
               ('iPad landscape 1024x768', 1024, 768, 'side'), ('iPad portrait 768x1024', 768, 1024, 'stacked'),
               ('8in landscape 1024x600', 1024, 600, 'side')]
    for label, vw, vh, expect in TABLETS:
        tctx = b.new_context(viewport={'width': vw, 'height': vh}, has_touch=True)
        tp = tctx.new_page()
        key = 'tab_%dx%d' % (vw, vh)
        tp.goto(H.page_url(key, fish, params={'shuffle': '0'}))
        tp.wait_for_selector('.dp-piece'); tp.wait_for_timeout(1100)
        st = tp.query_selector('#dp-stage').bounding_box()
        sc = tp.query_selector('#dp-scene').bounding_box()
        pcs = [e.bounding_box() for e in tp.query_selector_all('.dp-piece')]
        gm = tp.query_selector('#dp-game').bounding_box()
        side = all(q['x'] >= sc['x'] + sc['width'] - 1 for q in pcs)
        check('%s: whole puzzle visible without scrolling' % label, st['y'] >= 0 and st['y'] + st['height'] <= vh and st['x'] + st['width'] <= vw, (st, vh))
        check('%s: %s layout' % (label, expect), side == (expect == 'side'), (side, expect))
        check('%s: pieces inside the box' % label, all(q['x'] >= gm['x'] - 1 and q['x'] + q['width'] <= gm['x'] + gm['width'] + 1 and q['y'] >= gm['y'] - 1 and q['y'] + q['height'] <= gm['y'] + gm['height'] + 1 for q in pcs))
        check('%s: pieces big enough to grab (>= 80 px)' % label, min(q['width'] for q in pcs) >= 80, min(q['width'] for q in pcs))
        tx, ty = H.gap_center(tp, fish['params'])
        H.drag_to(tp, H.piece(tp, '1'), tx, ty)
        check('%s: drag works' % label, tp.evaluate('window.__answer') == '1')
        tp.screenshot(path=os.path.join(H.OUT, 'shot_' + key + '.png'))
        tctx.close()
    # rotating the tablet re-flows the layout
    rctx = b.new_context(viewport={'width': 1280, 'height': 800}, has_touch=True)
    rp = rctx.new_page()
    rp.goto(H.page_url('rotate', fish, params={'shuffle': '0'})); rp.wait_for_selector('.dp-piece'); rp.wait_for_timeout(1100)
    rp.set_viewport_size({'width': 800, 'height': 1280}); rp.wait_for_timeout(500)
    sc = rp.query_selector('#dp-scene').bounding_box()
    pcs = [e.bounding_box() for e in rp.query_selector_all('.dp-piece')]
    check('rotating landscape to portrait re-flows to stacked', all(q['y'] >= sc['y'] + sc['height'] - 1 for q in pcs))
    rctx.close()

    # ---------- 15. Real touch events ----------
    cdp = ctx.new_cdp_session(pg)
    open_item('touch', fish, params={'shuffle': '0'})
    tx, ty = H.gap_center(pg, fish['params'])
    ex, ey = H.center(H.piece(pg, '1'))
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': ex, 'y': ey}]})
    for i in range(1, 11):
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': ex + (tx - ex) * i / 10, 'y': ey + (ty - ey) * i / 10}]})
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    pg.wait_for_timeout(500)
    check('real touch drag works', pg.evaluate('window.__answer') == '1', pg.evaluate('window.__answer'))

    # ---------- 16. Shuffle ----------
    orders = set()
    for i in range(8):
        pg.goto(H.page_url('shuf', fish)); pg.wait_for_selector('.dp-piece')
        orders.add(tuple(e.get_attribute('data-id') for e in pg.query_selector_all('.dp-piece')))
    check('pieces are shuffled between children', len(orders) > 1, len(orders))

    check('no JavaScript errors in any run', not [e for e in errors if 'Failed to load resource' not in e and 'does not exist' not in e and 'drag-puzzle' not in e], errors[:3])
    b.close()

failed = results.count(False)
print('\n%d checks, %d failed' % (len(results), failed))
sys.exit(1 if failed else 0)
