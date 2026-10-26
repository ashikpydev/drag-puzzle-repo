# Data and analysis

## What is stored

The field is a normal `select_one`. The value saved is the choice value of the piece the child dropped in the gap.

| Situation | Stored value |
|---|---|
| Child drops the right piece first | the right piece's value (for example `1`) |
| Child drops a wrong piece first | that wrong piece's value (for example `3`) |
| Enumerator marks "could not do it" | `96` (change with `code_cannot`) |
| Enumerator marks "refused" | `97` (change with `code_refuse`) |
| Nothing done yet | empty (so `required` stops the enumerator moving on) |

Only the first piece dropped is stored by default, so the stored value is the child's first response. Set `record='last'` to store the final piece instead.

Tip: give the right piece the value `1` in every puzzle. The plug-in then needs no `correct=` setting, and in analysis "correct" is always `== 1`.

## Scoring

Because the answer is a coded choice, scoring is a simple comparison in your analysis software, not a form calculation. Examples in Stata (not run yet, adapt names to your data):

    * 1 = right piece dropped first, 0 = a wrong piece, missing = could not do it or refused
    gen puzzle_1_score = (puzzle_1 == 1) if inlist(puzzle_1, 1, 2, 3, 4)
    gen puzzle_1_special = puzzle_1 if inlist(puzzle_1, 96, 97)

Special codes are kept separate on purpose, so that "could not do it" and "refused" are never counted as a wrong answer.

If you want credit for a later right answer ("correct within 2 tries"), use the log below.

## The log (attempts, order, time)

Each puzzle also saves a log in the plug-in metadata, for example:

    v=1;status=correct;answer=3;correct=1;attempts=2;seq=3,1;moves=3;t_first=1.8;t_done=9.3;order=2,1,3,4

| Part | Meaning |
|---|---|
| `status` | `correct` (right piece dropped), `incorrect` (tries used up), `special` (enumerator code), `open` (still playing) |
| `answer` | The value stored in the field |
| `correct` | The value of the right piece |
| `attempts` | Number of pieces dropped in the gap |
| `seq` | The pieces dropped, in order |
| `moves` | Number of times a piece was picked up (includes drops outside the gap) |
| `t_first` | Seconds from opening the item to the first touch |
| `t_done` | Seconds from opening the item to the end |
| `order` | The left to right (or top to bottom) order the pieces were shown in |

To get the log into your dataset, add one calculate field per puzzle:

| type | name | calculation |
|---|---|---|
| calculate | puzzle_1_log | plug-in-metadata(${puzzle_1}) |

The sample form includes these. This is the only form expression the plug-in suggests, and it is optional. If you do not need attempts or timing, leave it out.

SurveyCTO documents `plug-in-metadata(field)` as the way other fields read plug-in metadata. Please check on a test export that the log column appears in your data before relying on it.

Examples in Stata (not run yet):

    gen p1_status   = regexs(1) if regexm(puzzle_1_log, "status=([a-z]+)")
    gen p1_attempts = real(regexs(1)) if regexm(puzzle_1_log, "attempts=([0-9]+)")
    gen p1_tfirst   = real(regexs(1)) if regexm(puzzle_1_log, "t_first=([0-9.]+)")
    gen p1_tdone    = real(regexs(1)) if regexm(puzzle_1_log, "t_done=([0-9.]+)")

## Notes on timing

`t_first` and `t_done` include time the child spends watching the entrance animation and any hand demo. They are best used to compare children on the same puzzle, not as precise reaction times. Time is measured from when the item opens on the screen, not from when the enumerator finishes reading the instruction.

## Revisiting an item

If the enumerator goes back to a puzzle that already has an answer, the plug-in shows the stored piece in the gap and locks the pieces. It does not let the child play again. To allow a retry, clear the answer in the form (the plug-in resets when SurveyCTO clears the field).
