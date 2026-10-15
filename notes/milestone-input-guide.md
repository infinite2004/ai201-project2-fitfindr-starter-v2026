# Milestone status and your input

## Milestone 1 — Completed

The data review is in `notes/milestone-1.md`. The original environment check
passed all 10 checks, including a model call. This was setup verification, not
an acceptance test of the then-unimplemented tools.

## Milestone 2 — Completed

README's Tool Inventory specifies typed inputs, outputs, empty cases, size
matching, and keyword ranking. The Planning Loop section states the branch
rule. These specifications were committed before implementation.

## Milestone 3 — Completed with your approval

You requested draft wording, reviewed it, and approved it for implementation.
The five criteria and reasons are in `criteria.md`, committed before tool
testing. The document and README explicitly acknowledge AI-assisted drafting;
they do not claim you independently authored the drafts.

## Milestone 4 — Implemented and tested

All three tools work independently. README's Sample Run contains actual
commands and outputs, including three uncached captions for the same input.
The empty wardrobe receives general suggestions, no matches return [], and
an empty outfit receives a descriptive message without a model call.

Your next review, if you want to change the style: read the three captions in
README and point to a sentence you like or want changed. Review the recorded
empty-wardrobe suggestions as well. AI inspection does not mean you personally
read them.

## Milestone 5 — Implemented and tested

The loop stores tool results in the session before the next call. A live run
verified that the selected listing reaches both downstream tools unchanged.
The impossible query stopped with zero model calls and a null fit card.
Full sessions and argument snapshots are in `results/milestone5-sessions.json`.
The offline suite passed 18 tests, with model responses mocked for regression
checks. These are build checks, not the later live acceptance evaluation.

The assignment's solo AI readability review is documented in README. The
empty-search message says to try broader keywords, a different size, or a
higher price limit. You can still share that message with your breakout group
and record what they would try next; no peer feedback has been fabricated.

## Personal reflection and later work

README's How I Used AI records the assistance and approval that actually
happened. It does not invent manual edits or personal testing. Add your own
observations after reviewing the outputs.

The CLI sample includes a literal Unicode escape in one generated caption;
that output is preserved as evidence of model formatting variability. Search
uses keyword overlap, so partial matches can appear below stronger matches.
The parser expects explicit size and price phrases, not arbitrary language.

Unit 4's five-trial live evaluation, MCP integration, before/after diagnosis,
and improvement sections remain unfilled. Those are later milestones, not
results that can be inferred from these implementation tests.
