# Assessment design notes

These notes are suggestions for using the game inside an ECD assessment. They are not validated. Item content, difficulty and scoring should be confirmed with the study's child development lead and pre-tested with children before any use in the field.

## Before the first scored item

* Start with a practice item (`practice=1`). It shows an animated hand, allows several tries, and puts the right piece in the gap if the child cannot do it.
* Do not use the practice result as a score.
* Let the child touch the tablet first. Sound starts only after the first touch.

## Enumerator protocol (suggested)

1. Read the question text aloud, in the child's language, exactly as written.
2. Do not point at or name the right piece.
3. Let the child play. Do not drag for the child.
4. If the child cannot do it or does not want to, tap the small gear button and choose "could not do it" or "refused". These are stored as `96` and `97` and kept apart from wrong answers.
5. Move to the next item only when the item shows the star or the gear status.

## Item design

* Put the right piece in a different screen position for different children. The plug-in shuffles pieces for you (`shuffle=0` turns this off).
* Avoid cues that are not part of the skill you measure, such as the right piece being the only one of its colour.
* Increase difficulty in steps: plain background wrong pieces first, near-miss pieces later.
* One piece per try is the default (`tries=1`), which gives a clean first-response score. Use more tries only if the construct needs it, and then use the log to see attempts.
* Keep the tablet on a table or the child's lap, with screen brightness high and volume at a level the room allows.

## Things to decide with the project team

* Scoring rule: first piece only, or credit within some number of tries.
* What `96` and `97` mean in analysis, and whether they are missing or zero.
* Which items are in baseline and which in endline (baseline and endline only, no midline), and whether the same pictures can be reused.
* Child assent and ethics approval for the game and for any timing data.
