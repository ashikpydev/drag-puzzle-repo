# Testing checklist for tablets

Run this on the oldest tablet and the newest tablet you plan to use, with the SurveyCTO Collect version you will use in the field. None of these steps have been done yet.

## Setup

- [ ] Upload the sample form and attach `drag-puzzle.fieldplugin.zip` and all files in `extras/sample-form/media`
- [ ] Download the form to the tablet and open it

## Display

- [ ] Pictures load (scene and all pieces)
- [ ] Landscape: picture left, pieces right, no scrolling needed
- [ ] Portrait: picture top, pieces below, no scrolling needed
- [ ] Rotating the tablet mid-item re-flows without losing the answer
- [ ] Gear button is visible and not covered by the navigation bar

## Play

- [ ] A finger drag picks up a piece and moves smoothly
- [ ] Dropping near the gap snaps; dropping far away bounces back
- [ ] Right piece: star, confetti, sound
- [ ] Wrong piece: shake and bounce back, the answer is stored
- [ ] Practice item: hand demo plays, restart works
- [ ] Sound is audible at room volume after the first touch; `sound=0` mutes

## Data

- [ ] Right piece stores its choice value; wrong piece stores that piece's value
- [ ] "Could not do it" stores 96, "refused" stores 97
- [ ] Going back to a finished item shows the answer and locks it
- [ ] Required stops the enumerator moving on without an answer
- [ ] Submit a test form and check the export: `select_one` column and the `plug-in-metadata` log column both appear
- [ ] Check the log values (attempts, seq, times) against what was done

## Children

- [ ] Cognitive pre-test with a few children from the target group: do they understand the task, are pieces large enough, any frightening sounds or animations
- [ ] Confirm ethics and consent arrangements
