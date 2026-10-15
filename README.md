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
> The standalone tools are implemented. The planning loop is next.
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

<!-- Three or four sentences: what a user asks for, and what they get back. -->



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

**Where it lives:** `agent.py::run_agent` (implementation follows Milestone 3).

**How the query is parsed:** Planned implementation uses regex, not a model.
Extract an optional price after `under`, `below`, `up to`, or `max`, allowing an
optional dollar sign and decimals. Extract an optional size after `size`,
including clothing alternatives, numeric shoe sizes, waist/length sizes, and
`One Size`. Remove the extracted phrases and use the remaining text as the
description. Missing size or price becomes `None`; price is a `float`.
The search ceiling is inclusive, including queries phrased as “under.”

**What moves through the session:** `query` and `wardrobe` start the session.
Parsed filters go in `parsed`, then search output in `search_results`, then the
first record in `selected_item`, then text in `outfit_suggestion`, and finally
text in `fit_card`. Each tool reads its arguments back from the session. The
empty-search path leaves `selected_item`, `outfit_suggestion`, and `fit_card`
as `None`. Each step will check the loop count with `trace.check_iterations`.

---

## Sample Run

**One full query**

The full-query run follows in Milestone 5, after the standalone tools below.

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

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
