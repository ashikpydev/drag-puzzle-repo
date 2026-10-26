# Development notes

## Layout

| Path | What it is |
|---|---|
| `source/` | The plug-in files: `manifest.json`, `template.html`, `script.js`, `style.css` |
| `drag-puzzle.fieldplugin.zip` | Built from `source/` (files at the zip root) |
| `extras/puzzle-maker/` | Offline puzzle maker page |
| `extras/sample-form/` | Sample form and pictures |
| `tools/` | Scripts that draw the sample pictures, build the sample form and make the previews |
| `tests/` | Automated checks |

## How it works

* Each piece is a choice of the `select_one`. Its image comes from `CHOICE_IMAGE`; the scene comes from `MEDIAIMAGE`.
* The gap position is set by `gap_x`, `gap_y`, `gap_w` (percent of the scene). The plug-in measures the screen and picks a side-by-side or stacked layout.
* Dragging uses Pointer Events. Animation uses CSS and the Web Animations API. Sounds are made with WebAudio and start after the first touch.
* On a drop, the plug-in calls `setAnswer` with the dropped piece's choice value, and saves a log with `setMetaData`.
* `window.clearAnswer` resets the game when SurveyCTO clears the field.

## Running the tests

Needs Python 3, `playwright` with Chromium, `openpyxl` and `Pillow`.

    cd tests
    python3 run_tests.py
    python3 run_maker_tests.py

The tests load the real sample form, mock the SurveyCTO plug-in API, and drive the page with Chromium. They do not replace a test in SurveyCTO Collect.

## Rebuilding the zip

    cd source
    zip -X ../drag-puzzle.fieldplugin.zip manifest.json template.html script.js style.css

Files must be at the zip root. Bump `version` in `manifest.json` and add a line to `CHANGELOG.md` for each release.

## Regenerating the sample form and previews

    python3 tools/make_sample_pictures.py
    python3 tools/make_sample_form.py
    python3 tools/make_preview.py
