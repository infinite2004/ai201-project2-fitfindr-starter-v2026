# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> The tools and planning loop are implemented. See the real sample runs below.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

FitFindr searches 40 sample thrift listings from a plain-language clothing
request, with optional size and price limits. It selects the highest-ranked
keyword match, suggests outfits using an example wardrobe, and generates a
short fit card with the item's price and platform. If no listing matches, it
stops before either model call and suggests how to adjust the search.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Loads listings with `utils.data_loader.load_listings`, applies the size and inclusive price ceiling, then ranks matches by keyword overlap.
- **Inputs:** `description: str`; `size: str | None = None`; `max_price: float | None = None`. Description words are case-insensitive alphanumeric tokens. Ignore the filler words `a`, `an`, `the`, `and`, `or`, `for`, `of`, `in`, `on`, `with`, `me`, `find`, `looking`, `want`, `i`, `some`, `please`.
- **Returns:** `list[dict]`, with at most `config.SEARCH_RESULT_LIMIT` complete listing records. Each record contains `id: str`, `title: str`, `description: str`, `category: str`, `style_tags: list[str]`, `size: str`, `condition: str`, `price: float`, `colors: list[str]`, `brand: str | None`, and `platform: str`. Score one point per distinct query token present in the title, description, category, tags, colors, or non-null brand. Keep scores above zero; sort descending by score and preserve dataset order for ties. All returned records must satisfy both supplied filters.
- **When it has nothing:** Return `[]` when nothing matches or no meaningful description tokens remain; never return `None` for an empty search.

Size matching is case-insensitive, with surrounding whitespace removed. Remove
parenthesized fit notes, then split alternatives at `/`. Clothing sizes must
match a whole alternative: `M` matches `S/M`, but `L` does not match `XL` and `S`
does not match `US 9`. Numeric shoe sizes accept an optional `US` prefix (`8`
matches `US 8`, not `US 8.5`). A waist-only request such as `W30` matches `W30`
or `W30 L30`; a waist-and-length request must match both. `One Size` matches a
whole `One Size` alternative. `None` skips that filter. A price exactly equal
to `max_price` is included. The search is keyword overlap, not semantic search;
one matching meaningful token is enough, so broad queries may include partial
matches.

### `suggest_outfit`

- **What it does:** Calls the starter's `generate()` adapter to suggest one or two outfits built around the selected listing.
- **Inputs:** `new_item: dict` with the listing fields above; `wardrobe: dict` containing `items: list[dict]`. Each wardrobe item has `id: str`, `name: str`, `category: str`, `colors: list[str]`, `style_tags: list[str]`, and optional `notes: str | None`.
- **Returns:** A non-empty `str` naming the selected item and suggesting combinations. With a populated wardrobe, the prompt asks for specific pieces by their recorded names and does not claim additional pieces are owned. Null brand and notes values are omitted from prose. The tool leaves both input dictionaries unchanged.
- **When it has nothing:** With `{"items": []}`, ask the model for general styling advice and label suggested companion pieces as ideas, not owned items. With no selected item (`{}`), return `No item selected. Search for an item before requesting outfit advice.` without a model call. If the model returns blank text, return `No outfit advice was generated. Try again.` A connection or authentication failure from the adapter remains `ModelUnavailable`, not a successful suggestion.

### `create_fit_card`

- **What it does:** Calls `generate()` to turn an outfit suggestion and selected listing into a short caption.
- **Inputs:** `outfit: str`; `new_item: dict` with the listing fields above.
- **Returns:** A non-empty `str`. The prompt requests a two-to-four-sentence caption naming the item, price, and platform once each, with a concrete style description and no invented brand or ownership claims. These are prompt requirements; model adherence still needs to be tested. The tool leaves the listing unchanged.
- **When it has nothing:** If `outfit` is empty or whitespace-only, return `No outfit suggestion available. Generate an outfit before creating a fit card.` without calling the model. If `new_item` is `{}`, return `No item selected. Search for an item before creating a fit card.` without a model call. If the model returns blank text, return `No fit card was generated. Try again.` Adapter failures remain `ModelUnavailable`.

---

## Planning Loop

**Branch rule:** If `search_listings` returns an empty list, store a message in
`session["error"]` that suggests changing the description, size, or price limit,
and return immediately without calling either model tool. Otherwise, store the
first result in `session["selected_item"]`, call `suggest_outfit`, store its
output, then call `create_fit_card` using the stored outfit and selected item.
Store the card and return the session.

**Where it lives:** `agent.py::run_agent`.

**How the query is parsed:** `agent.py::parse_query` uses regex, not a model.
Extract an optional price after `under`, `below`, `up to`, or `max`, allowing an
optional dollar sign and decimals. Extract an optional size after `size`,
including clothing alternatives, numeric shoe sizes, waist/length sizes, and
`One Size`. Remove the extracted phrases and use the remaining text as the
description. Missing size or price becomes `None`; price is a `float`.
The search ceiling is inclusive, including queries phrased as “under.”
The parser handles one size clause and one price clause; it is not a general
natural-language interpreter. Without the `size` keyword, size is not extracted.
Requested alternatives such as `S/M` match either whole size alternative.

**What moves through the session:** `query` and `wardrobe` start the session.
Parsed filters go in `parsed`, then search output in `search_results`, then the
first record in `selected_item`, then text in `outfit_suggestion`, and finally
text in `fit_card`. Each tool reads its arguments back from the session. The
empty-search path leaves `selected_item`, `outfit_suggestion`, and `fit_card`
as `None`. Blank model responses stop with an explanatory error; a
`ModelUnavailable` failure preserves prior state and returns a message about
checking the key, model setting, and connection. Each step checks the loop count with `trace.check_iterations`.

---

## Sample Run

**One full query**

```bash
$ AI201_CACHE=0 python app.py ask 'vintage graphic tee under $30'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Outfit 1:
- Selected Item: Y2K Baby Tee — Butterfly Print
- Companion Pieces: Baggy straight-leg jeans, dark wash; Chunky white sneakers
- Style: A quintessential Y2K streetwear look that balances the fitted, cropped silhouette of the baby tee with relaxed, high-waisted denim and chunky sneakers.

Outfit 2:
- Selected Item: Y2K Baby Tee — Butterfly Print
- Companion Pieces: Wide-leg khaki trousers; Chunky white sneakers
- Style: A minimal, earth-toned take that pairs the vintage graphic tee with tailored wide-leg trousers for an effortless, casual aesthetic.

  Fit card: This casual Y2K streetwear look pairs the Y2K Baby Tee \u2014 Butterfly Print found on depop for $18.00 with baggy straight-leg jeans in a dark wash and chunky white sneakers. The fitted, cropped silhouette of the graphic tee balances the relaxed denim for a quintessential early 2000s aesthetic. Alternatively, the vintage top can be styled with wide-leg khaki trousers and chunky white sneakers for a minimal, earth-toned take.

2 model calls this session, 1206 prompt + 233 output tokens
```

**An impossible query**

```bash
$ AI201_CACHE=0 python app.py ask 'designer ballgown size XXS under $5'

  No listings matched your search. Try broader description keywords, a different size, or a higher price limit.

0 model calls this session
```

The instrumented live run in
[results/milestone5-sessions.json](results/milestone5-sessions.json) records the
complete sessions and snapshots of the actual arguments received by both model
tools. Both received `lst_002`, the same complete listing stored in
`session["selected_item"]`; the card tool also received the stored outfit.
The happy path made two model calls. The impossible query made zero model calls
and left `selected_item`, `outfit_suggestion`, and `fit_card` as `None`.
Reproduce this evidence with `python scripts/milestone5_samples.py`.

The CLI caption above contains a literal `\u2014` despite readable Unicode in
the prompt. The raw response is preserved here rather than silently corrected.
Model wording and formatting remain variable; the five-trial acceptance
measurement is recorded in the Unit 4 sections below.

**Empty-search message review (solo AI option)**

Given only the displayed message, the next actions I would try are broader
keywords, another size, or a higher price limit. This is an AI readability
review, not feedback from a breakout group or a claim of personal user testing.
The message names concrete actions a user can take.

**Offline verification**

At Milestone 5, `python -m unittest discover -s tests -v` passed 18 tests. The checks include
five matching queries with snapshots of the actual tool inputs, five empty
queries with model tools asserted uncalled, and five price ceilings with known
matches. Model responses are mocked for these regression checks, so their
results do not establish live-model success rates. See
[results/milestone5-unit-tests.txt](results/milestone5-unit-tests.txt).


**The three tools, tested one at a time**

The following are actual terminal commands and outputs. `AI201_CACHE=0`
disables cached answers; `TEMPERATURE` remains 0.9. The search display shows
ID, title, size, price, and platform; the function returns full listing dicts.

```bash
$ AI201_CACHE=0 python -c 'from tools import search_listings; print([(x['"'"'id'"'"'], x['"'"'title'"'"'], x['"'"'size'"'"'], x['"'"'price'"'"'], x['"'"'platform'"'"']) for x in search_listings('"'"'graphic tee'"'"', size='"'"'M'"'"', max_price=30)])'
[('lst_002', 'Y2K Baby Tee — Butterfly Print', 'S/M', 18.0, 'depop'), ('lst_017', 'Mesh Long-Sleeve Top — Black', 'S/M', 15.0, 'depop')]
```

```bash
$ AI201_CACHE=0 python -c 'from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))'
**Outfit 1:**
* **Selected Item:** Vintage Levi's 501 Jeans — Medium Wash
* **Companion Pieces:** White ribbed tank top, Vintage black denim jacket, Chunky white sneakers, Black crossbody bag
* **Style:** Casual Streetwear. This look pairs the classic vintage denim with a fitted basic top and a slightly cropped jacket, finished off with chunky sneakers and a minimal crossbody bag for an effortless, everyday vibe.

**Outfit 2:**
* **Selected Item:** Vintage Levi's 501 Jeans — Medium Wash
* **Companion Pieces:** Oversized grey crewneck sweatshirt, Black combat boots, Brown leather belt
* **Style:** Cozy Grunge. The relaxed, oversized grey sweatshirt contrasts with the structure of the straight-leg 501s and the edgy lace-up boots, pulled together with a classic brown leather belt.
```

```bash
$ AI201_CACHE=0 python -c 'from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('"'"'jeans and white sneakers'"'"', load_listings()[0]))'
Pair the Vintage Levi's 501 Jeans — Medium Wash with clean white sneakers for a classic, effortless streetwear look. The faded indigo denim brings an authentic vintage feel to the casual outfit. Find this piece on depop for $38.00.
```

**Same fit-card input, two additional uncached runs**

```bash
$ AI201_CACHE=0 python -c 'from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('"'"'jeans and white sneakers'"'"', load_listings()[0]))'
This casual streetwear fit pairs the Vintage Levi's 501 Jeans — Medium Wash with clean white sneakers. The classic denim features light fading at the knees for an authentic worn-in look. You can find this piece for $38.0 on depop.
```

```bash
$ AI201_CACHE=0 python -c 'from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('"'"'jeans and white sneakers'"'"', load_listings()[0]))'
The Vintage Levi's 501 Jeans — Medium Wash are listed on depop for $38.0. This classic streetwear outfit pairs the blue denim bottoms with casual white sneakers. The light fading at the knees enhances the vintage aesthetic of the look.
```

All three captions differ. Each has three sentences, identifies the same
Levi's jeans, and mentions the $38 price and depop once. These three build
samples are not the five-trial Unit 4 acceptance evaluation.

**Empty cases**

```bash
$ AI201_CACHE=0 python -c 'from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_empty_wardrobe()))'
The Vintage Levi's 501 Jeans — Medium Wash are a versatile classic with a medium wash and light fading at the knees.

**Styling Ideas:**

1. **Casual Streetwear:** Pair the jeans with a tucked-in graphic tee and a leather belt to highlight the vintage fit. Consider adding a classic canvas sneaker and a unstructured tote bag as suggestion pieces.
2. **Layered Neutral:** Style the denim with an oversized knit sweater half-tucked at the waist. Consider adding a tailored trench coat and leather loafers as suggestion pieces to elevate the look.
```

```bash
$ AI201_CACHE=0 python -c 'from tools import search_listings; print(search_listings('"'"'designer ballgown'"'"', size='"'"'XXS'"'"', max_price=5))'
[]
```

```bash
$ AI201_CACHE=0 python -c 'from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('"'"'   '"'"', load_listings()[0]))'
No outfit suggestion available. Generate an outfit before creating a fit card.
```

The empty wardrobe gets suggestions without claiming the pieces are owned.
The impossible search returns `[]`. A missing outfit returns a useful message
without a model call. Eleven offline regression tests also passed; their
output is in [results/milestone4-unit-tests.txt](results/milestone4-unit-tests.txt).
Raw sample output is in [results/milestone4-tools.json](results/milestone4-tools.json).
Reproduce with `python scripts/milestone4_samples.py` from an activated environment.

---

## How I Used AI

**Moment 1 — Specifications and criteria**

- *What I asked for:* Help following each milestone, identifying where my input was needed, and drafting suitable acceptance-criterion wording.
- *What came back:* A typed tool inventory, an explicit empty-search branch rule, and draft criteria covering full runs, early stops, state, caption quality, and price limits.
- *What I changed:* I approved the draft wording and asked for implementation. I did not independently rewrite the criteria; `criteria.md` records that they were AI-assisted and approved before implementation tests.

**Moment 2 — Implementation and evidence**

- *What I asked for:* Implement the approved plan and continue the milestones.
- *What came back:* Codex implemented the tools and session-based loop, added offline regression tests, and saved actual uncached model outputs. During sample review it found a literal escaped dash in a generated caption, changed JSON prompt formatting to preserve Unicode, and refreshed the samples.
- *What I changed:* I delegated implementation rather than making manual code edits. The code changes and test execution described here were performed by Codex; this does not claim a peer review or a personal edit I did not make.

## Run Log — Before

Repository to submit: https://github.com/infinite2004/ai201-project2-fitfindr-starter-v2026

`criteria.md` is byte-for-byte unchanged from the previous unit (`4085a0d`).
The table shows the three runs requested by this submission checklist. Because
the existing criteria require five, two supplemental trials are shown separately;
verdicts use all five, not an extrapolation from three.

```bash
source .venv/bin/activate
python run_eval.py --label before
```

The run used `gemini-3.5-flash-lite`, temperature 0.9, with caching OFF.
The fixed inputs are in `scenarios.py`. Criterion 3 observes the same five live
agent runs as criterion 1; these are shared observations, not independent extra
runs or cached model responses. Criterion 4 uses the same `lst_001` jeans and
`jeans and white sneakers` outfit for all five generations. Criterion 5 uses
five known matches at different exact-price ceilings: $18, $22, $24, $32, $45.

| Criterion | Original target | Try 1 | Try 2 | Try 3 | Verdict (all 5) |
|---|---|---|---|---|---|
| 1. matching query completes | 4/5 | PASS | PASS | PASS | MET (4/5) |
| 2. impossible query stops early | 5/5 | PASS | PASS | PASS | MET (5/5) |
| 3. selected item preserved | 5/5 | PASS | PASS | PASS | MISSED (4/5) |
| 4. short grounded fit card | 4/5 | FAIL | PASS | FAIL | MISSED (3/5) |
| 5. inclusive price ceiling | 5/5 | PASS | PASS | PASS | MET (5/5) |

Supplemental trials needed to apply the unchanged five-trial targets:

| Criterion | Try 4 | Try 5 |
|---|---|---|
| 1 | PASS | FAIL |
| 2 | PASS | PASS |
| 3 | PASS | FAIL |
| 4 | PASS | PASS |
| 5 | PASS | PASS |

**Actual baseline output**, criterion 4, try 3, produced by
`tools.py::create_fit_card` through `run_eval.py::run_trial`:

```text
Style the Vintage Levi's 501 Jeans — Medium Wash with the included jeans and white sneakers for a classic streetwear look. This casual outfit features the medium wash denim paired with clean white sneakers. You can find this pair listed on depop for $38.00.
```

Actual recorded fields from criterion 1/3, try 5, produced by
`agent.py::run_agent` and captured by `run_eval.py::observe_agent`:

```json
{
  "query": "denim jacket under $50",
  "selected_item_id": "lst_007",
  "actual_calls": [
    "search_listings",
    "suggest_outfit"
  ],
  "outfit_suggestion": null,
  "fit_card": null,
  "error": "The model is unavailable. Check your API key, model setting, and internet connection, then try again."
}
```

Full text log: [before run](results/run_20261015T010935709469Z_before.md).
Raw sessions and actual call arguments: [before JSON](results/run_20261015T010935709469Z_before.json).
The baseline made 14 model calls: the fifth full run failed before its second
call, so that request never happened. Failed runs were retained, not replaced.

## Verdicts

| Criterion | Before | After | How the verdict was decided |
|---|---|---|---|
| 1 | MET (4/5) | MET (5/5) | Actual call records show all three tools and a non-empty card in 4/5 before and 5/5 after; target is 4/5. |
| 2 | MET (5/5) | MET (5/5) | Every trial calls only search, leaves the card null, and names changes to description, size, or budget. |
| 3 | MISSED (4/5) | MET (5/5) | Compared id, title, price, size, and platform in the actual downstream arguments against selected_item. One baseline run never reached the card tool; all five after-runs did. |
| 4 | MISSED (3/5) | MET (5/5) | Counted sentences, item identification, price and platform mentions, then reviewed factual claims. Two baseline captions implied included or bundled merchandise; none did afterward. |
| 5 | MET (5/5) | MET (5/5) | Each of five different ceilings retained its known matching item and all returned prices were within budget, including equality at the boundary. |

Caption checking has two parts. `run_eval.py` records mechanical checks and
provisional results; those checks alone passed all five baseline captions.
An AI text review then applied the original criterion's rule that incorrect
factual details fail. It conservatively failed ambiguous bundle availability
and unsupported inclusion claims. The exact wording and reasoning are saved in
[before caption review](results/before-caption-review.json) and
[after caption review](results/after-caption-review.json). This is AI-assisted
assessment, not a claim of human or peer review. A reader can audit or disagree
with the interpretation; the raw output is preserved.

The combined results are [before reviewed](results/run_20261015T010935709469Z_before_reviewed.json)
and [after reviewed](results/run_20261015T011901657706Z_after_reviewed.json). No original log was
rewritten to hide the difference between mechanical checks and factual review.

## Diagnoses

- **Criterion 3 — model generation stage, before try 5:** Search selected
  `lst_007`, and `suggest_outfit` received its correct fields. A
  `ModelUnavailable` exception then caused the loop to return before
  `create_fit_card`. The criterion requires both downstream calls, so this is
  a failed trial even though no item mutation was observed. The same event is
  criterion 1's allowed single failure. The saved generic error does not reveal
  the underlying HTTP or network cause; the evidence does not establish a bad
  key, quota problem, or specific service failure.
- **Criterion 4 — model output shaped by the fit-card prompt, before tries 1
  and 3:** The prompt supplies both merchandise facts and outfit suggestions
  without explicitly separating their roles. Try 1 says the “relaxed pairing”
  is available for the listed price; under the conservative grounding review,
  that implies a bundle unsupported by the listing. Try 3 calls companion
  pieces “included.” The price is numerically correct, but the claim about
  what is for sale is not supported. This is not a search or state-transfer
  error: the correct listing reached the tool.

The diagnosis and planned change were committed before changing the prompt:
[baseline note](notes/unit4-baseline.md), commit `c804741`.

## The Improvement

Changed only the prompt in `tools.py::create_fit_card` (commit `6452ade`).
It now states that the selected item is the only item for sale, attaches price
and platform to that item in one sentence, and describes companion styling in
a separate sentence. It forbids claims that companions are included or bundled
and clarifies that “jeans” in the outfit may refer to the selected jeans.

This targets criterion 4's observed merchandise/styling confusion. It does not
change search, session handling, model settings, or the acceptance criteria.
Source hashes in both logs verify that criteria, agent, scenarios, and runner
were unchanged between runs; only the tool prompt changed.

### Run Log — After

```bash
source .venv/bin/activate
python run_eval.py --label after
```

| Criterion | Original target | Try 1 | Try 2 | Try 3 | Verdict (all 5) |
|---|---|---|---|---|---|
| 1. matching query completes | 4/5 | PASS | PASS | PASS | MET (5/5) |
| 2. impossible query stops early | 5/5 | PASS | PASS | PASS | MET (5/5) |
| 3. selected item preserved | 5/5 | PASS | PASS | PASS | MET (5/5) |
| 4. short grounded fit card | 4/5 | PASS | PASS | PASS | MET (5/5) |
| 5. inclusive price ceiling | 5/5 | PASS | PASS | PASS | MET (5/5) |

Supplemental trials needed to apply the unchanged five-trial targets:

| Criterion | Try 4 | Try 5 |
|---|---|---|
| 1 | PASS | PASS |
| 2 | PASS | PASS |
| 3 | PASS | PASS |
| 4 | PASS | PASS |
| 5 | PASS | PASS |

**Actual after output**, criterion 4, try 3, from
`tools.py::create_fit_card` through `run_eval.py::run_trial`:

```text
Grab the Vintage Levi's 501 Jeans — Medium Wash for $38.0 on depop to nail this classic streetwear look. The medium wash denim pairs effortlessly with crisp white sneakers for an easy, everyday outfit.
```

Full text log: [after run](results/run_20261015T011901657706Z_after.md).
Raw sessions and tool arguments: [after JSON](results/run_20261015T011901657706Z_after.json).
This run made 15 uncached model calls. Both sets use the same five inputs,
review rule, model, and temperature. No failed trial was silently rerun.

**Did it help?** Caption grounding improved from 3/5 to 5/5 in these samples,
with the same AI review rule. This supports the prompt change for the tested
item and outfit; five stochastic samples do not establish a general success
rate or prove causation. Criterion 3 also rose from 4/5 to 5/5, but the prompt
change did not address availability, so that recovery is not evidence it fixed
the earlier model failure. The 22 offline regression tests also passed; see
[regression output](results/unit4-regression-tests.txt).

## What's Still Broken

None of the five criteria missed its target in the after-run. That does not
mean every known issue is fixed:

- The baseline model-unavailable event remains unexplained. Next I would retain
  safe error categories/status codes and evaluate bounded retries for transient
  failures. I left that unchanged to isolate the one prompt improvement.
- The literal Unicode escape seen in the previous unit still survives the
  separately labelled replay diagnostic in both logs. This diagnostic uses a
  mocked, previously recorded response, not a fresh model trial. A focused
  punctuation-normalization fix and its tests would be separate work; it is
  outside the five current targets and was not mixed into this comparison.
- Keyword overlap can return partial matches, and the parser supports explicit
  size/price phrases rather than arbitrary language. Price compliance does not
  prove relevance. Those rules remain unchanged for the controlled comparison.
- Caption grounding was tested on one item/outfit pair. A different product or
  longer outfit could still create an unsupported claim. Next I would evaluate
  more items and write an explicit factual-claim checklist before scoring.

## What I'd Do Differently

*AI-assisted reflection draft based on these results:*

I would write criterion 3 differently next unit so it distinguishes state
integrity from service availability. Here, an unavailable model prevented the
second comparison even though the selected item was not observed changing.
I would check state invariants on each actual call and track completion and
availability separately, with both targets fixed in advance.

I would also make criterion 4's factual-review rules more explicit before the
run: only the selected item has the listed price, and companion clothing is
not included merchandise. The baseline showed that correct numbers can still
appear in a misleading sentence. I would specify how to treat ambiguous bundle
claims and test more than one item/outfit combination. These are proposals for
next unit, not revisions to the current targets.

Finally, I would align the trial count in the submission instructions and the
criteria before collecting results. This submission preserves five-trial
targets with two supplemental trials rather than quietly lowering them to three.

This unit adds four commits after `4085a0d`: evaluation cases and capture,
baseline and diagnoses, the prompt improvement, and the after-results plus this
submission write-up. The original repository and previous-unit history remain
intact. No API key, `.env`, or virtual environment is included.

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
