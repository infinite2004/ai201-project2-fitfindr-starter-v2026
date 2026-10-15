# Baseline recorded before the improvement

Command: `python run_eval.py --label before`.
Raw evidence: `results/run_20261015T010935709469Z_before.json` and `.md`.
All model calls were uncached, at temperature 0.9. There were 14 real calls:
one matching run stopped after its first model call, so the planned fifteenth
call never happened. Criteria 1 and 3 inspect the same five agent runs.

| Criterion | Original target | Try 1 | Try 2 | Try 3 | Supplemental 4 | Supplemental 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Full run | 4/5 | PASS | PASS | PASS | PASS | FAIL | MET (4/5) |
| 2. Empty search | 5/5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. State | 5/5 | PASS | PASS | PASS | PASS | FAIL | MISSED (4/5) |
| 4. Fit card | 4/5 | FAIL | PASS | FAIL | PASS | PASS | MISSED (3/5) |
| 5. Budget | 5/5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

The assignment asks for three displayed trials; the two supplemental trials
make the original five-trial targets measurable without rewriting criteria.

## Diagnosis of misses

Criterion 3, try 5: search selected `lst_007` and `suggest_outfit` received the
same fields. The model adapter then raised `ModelUnavailable`; the loop handled
it and never called `create_fit_card`. This is an unavailable generation stage,
not evidence of a mutated item. Since both downstream calls are required by the
original criterion, the try fails. The saved session has only the generic
message, so the underlying HTTP/network cause cannot be established from this
log. It would be wrong to assert that the key, quota, or network was at fault.
This same event is criterion 1's one failed try, within its 4/5 allowance.

Criterion 4: all five captions met the mechanical sentence/item/price/platform
checks. A separate AI text review applied the criterion's existing rule that
incorrect factual details fail. Try 1 says, "This relaxed pairing is available
on depop for $38.0," which conservatively fails because it attaches listing
availability to the pairing, not just the jeans. Try 3 says, "with the included
jeans and white sneakers," inventing included companion clothing. The review
is explicitly an interpretation of the visible wording; it is not a human or
peer review. Every decision is recorded in `results/before-caption-review.json`.
Raw mechanical records are unchanged; `*_before_reviewed.json` contains the
combined verdicts.

Pipeline stage and mechanism: `tools.py::create_fit_card` sends both the listing
and outfit to the model. Its prompt asks for facts and style but does not make
the distinction between merchandise for sale and companion styling ideas
explicit enough. The output blends those roles and creates a bundle claim.

## Chosen improvement and prediction

Change only the fit-card prompt: explicitly state that price/platform apply
only to the selected item, companions are not included merchandise, and a
reference to jeans in the outfit can refer to the selected jeans rather than
an additional pair. Ask for the listing fact and styling advice in separate
sentences. Keep model, temperature, data, search, loop, scenarios, criteria,
review rule, and number of trials unchanged.

Prediction: fewer unsupported inclusion/bundle claims in criterion 4. This
prompt change does not address model availability, so a better criterion 3
result afterward cannot be attributed to it.

A separate replay of the previous unit's captured caption reproduces a literal
Unicode escape. It is labelled as mocked replay, not fresh model evidence, and
is outside the five criteria. It is not the chosen improvement in this unit.
