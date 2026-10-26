# Making a puzzle

## The quick way: the puzzle maker

1. Open `extras/puzzle-maker/puzzle-maker.html` in any browser. Nothing is uploaded, it works offline.
2. Choose your picture. It must be a **complete picture with no gap**. PNG, JPG, GIF and WebP are accepted.
3. Drag the **green GAP box** over the part the child must find. This becomes piece 1, the right piece.
4. Drag the **red boxes** to places that make good wrong pieces. Use "Add wrong piece" for more. Three wrong pieces (four pieces in total) is a good size for young children.
5. Use the width slider to set the piece size. Pieces that are 20 to 25 percent of the picture width work well.
6. Fill in the item settings: field name, the question text the enumerator reads, tries, practice, and look.
7. Click **Download puzzle files (zip)**.

The zip contains:

| File | What it is |
|---|---|
| `<name>_scene.png` | Your picture with the gap painted white. Goes in the `media:image` column. |
| `<name>_p1.png` | The right piece, cut exactly from your picture. |
| `<name>_p2.png` onwards | Wrong pieces. |
| `<name>_form_rows.txt` | The survey row and the choices rows, tab separated, ready to paste into Excel. |

The page also shows the **appearance setting** to copy, for example
`custom-drag-puzzle(gap_x=43.3, gap_y=31.7, gap_w=22, correct=1)`.

Attach all PNG files to your form like any other attachment, and attach `drag-puzzle.fieldplugin.zip` as the field plug-in.

## Choosing a good picture

* Use clear, simple scenes with a few large objects. Small details are hard for young children to match.
* Put the gap over something with a distinctive feature (an eye, a door handle, a pattern), so the right piece can be recognised by looking.
* Good wrong pieces are plausible but clearly different. A "near miss" cut from beside the gap is a good harder item. A piece of plain background is a good easy item.
* Avoid making the right and wrong pieces differ only by red versus green, which some children cannot tell apart.
* Use your own artwork or properly licensed pictures. Stock images with watermarks cannot be used.
* File names: letters, numbers, dot, dash and underscore only, starting with a letter. No spaces. Names are case sensitive.
* The maker shrinks pictures to 1000 pixels wide by default so they load quickly on tablets. Change this if you need more detail.

## If an artist already gave you the pieces

You do not have to use the maker. You need:

1. **A scene picture** that already shows the empty space. Put its file name in the `media:image` column.
2. **One image per piece**, each cut to the same shape as the empty space. Put each file name in the `image` column of the choices sheet.
3. **The gap position** in the appearance column: `gap_x` and `gap_y` are the top-left corner of the empty space and `gap_w` is its width, all in percent of the scene picture. To find these numbers, load the scene picture in the puzzle maker and move the green box over the empty space, then read the numbers from the appearance setting.
4. `correct=` set to the value of the right choice (for example `correct=3`).

Pieces are stretched to fit the gap shape, so cut them with the same width to height ratio as the gap.

## Several puzzles in one form

Make one `select_one` question per puzzle, each with its own choices list and its own picture files. Use different file names for each puzzle. The sample form has three.

## Audio instruction (optional)

Put a recording in the `media:audio` column of the question. A small speaker button appears on the puzzle. A child (or the enumerator) can tap it to hear the instruction again. Sound does not play by itself, because tablets block audio until the screen is touched.

## Setting the look

Add `theme='candy'` (or `'forest'`, `'ocean'`, `'sunny'`, `'sky'`) to the appearance. Use different themes in one form to keep children interested, or one theme for the whole assessment for consistency.

## Practice items

Set `practice=1`. A practice item allows up to 9 tries, shows an animated hand demonstrating the drag, places the right piece in the gap if the child runs out of tries, and gives the enumerator a restart button. Put the practice item first and do not use its result as a score.
