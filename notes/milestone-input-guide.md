# Milestones and your input

## Milestone 1 — Read data and run the starter

Completed. See `notes/milestone-1.md`. The environment check passed all 10
checks, including a real model call. That setup check is not an acceptance
criterion result for the unbuilt tools.

## Milestone 2 — Tool specification

The Tool Inventory and Planning Loop sections in `README.md` are filled in.
No personal input was required to specify the starter's interfaces. Optional:
read the size-matching and keyword-ranking rules and say if you want a different
behavior before implementation.

## Milestone 3 — Acceptance criteria: your input required

The assignment says not to ask a model to write these criteria. It also says
they must exist before testing. `criteria.md` is intentionally still yours to
complete; no targets or personal reasons have been invented for you.

Open `criteria.md` and keep the two supplied criteria. Under each, explain why
its target is appropriate. Write your three criteria under sections 3, 4, and
5, and give a reason under each one. You can instead send the following filled
outline in chat for insertion into that file:

- Criterion 1 reason: ___
- Criterion 2 reason: ___
- Criterion 3 (state): Given ___, compare ___ with ___; pass when ___,
  in ___ of 5 tries. Reason: ___
- Criterion 4 (fit card): Given ___, inspect ___; pass when ___,
  in ___ of 5 tries. Reason: ___
- Criterion 5 (your choice): Given ___, observe ___; pass when ___,
  in ___ of 5 tries. Reason: ___

For state, think about how you would identify the item at each step. For the
fit card, decide what would make a caption useful even if its wording changes.
For your choice, pick a behavior you care about. Set the targets yourself.

After you write them, the AI can explain exactly how each sentence could be
tested without suggesting replacements. You decide any changes and the final
wording. The criteria should then be committed before tool testing starts.

## Milestone 4 — Implement and test individual tools

The implementation and terminal checks can be done by the AI after Milestone 3.
It will save actual commands and output in README's Sample Run, exercise empty
cases, and run the same fit-card input three times with caching disabled.
`TEMPERATURE` is currently 0.9; caching is enabled by default.

Your review: read the three captions and decide whether their style is useful.
You can point to a specific sentence and explain what you like or want changed.
If you edit prompts yourself, describe the change in README's How I Used AI.
Do not claim to have read outputs you have not seen.

## Milestone 5 — Connect the planning loop

Implementation and the happy/empty-path checks can be done by the AI after
Milestone 4. The checks need to show that tool inputs come from the session,
and that the empty-search path leaves the fit card as None.

For the discussion, share the branch rule and actual empty-search message with
your group, or use the assignment's solo AI review option. Say what you would
try next after reading the message. Any changes to the message should reflect
your decision. Technical checks and this discussion are separate evidence.

## Personal reflection and submission

README's How I Used AI asks what you asked, what came back, and what you changed.
The AI can record the assistance it actually provided, but your own review and
changes must come from you. If you changed nothing, say that accurately.

Unit 4 evaluation, MCP integration, and before/after verdict sections are not
part of these pasted milestones and should remain unfilled for now.
