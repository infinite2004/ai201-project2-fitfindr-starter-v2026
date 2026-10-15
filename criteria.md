# Acceptance criteria — FitFindr

These five targets were approved before implementation testing. The student
reviewed and accepted AI-assisted draft wording; the targets below record that
choice rather than claiming the drafts were written without assistance.
Run model-based trials with caching disabled. These are targets, not results.

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a non-empty fit card — in at least 4 of 5 tries.

**Why this target:** I chose 4 out of 5 because the full run depends on keyword
matching and two model-generated responses. Different query wording can affect
search results, and generation can occasionally fail. Four successful runs is
a useful initial target while still making failures visible. A completed run
must call all three tools and return a non-empty fit card, not merely avoid
crashing.

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit`, leaves `fit_card` as `None`, and returns a message naming
what to change — 5 of 5 tries.

**Why this target:** I chose 5 out of 5 because this branch uses a fixed
condition: whether the search result is an empty list. It does not need the
model to make a decision. Every empty search should stop and tell the user to
change their description, size, or price limit.

## 3. The selected item stays the same between tools

Across five matching queries, the listing passed to `suggest_outfit` and
`create_fit_card` must have the same `id`, `title`, `price`, `size`, and
`platform` as `session["selected_item"]` in 5 of 5 runs.

**Why this target:** Passing stored data between functions is deterministic.
A different item or changed price would mean the agent is recommending
something other than the selected listing.

**How to check:** Record the actual arguments received by both tools and
compare them with the session.

## 4. Fit cards are short and grounded in the listing

For five uncached generations using the same valid item and outfit, at least
4 of 5 fit cards must contain two to four sentences, identify the selected
item, and mention its correct price and platform once each.

**Why this target:** The wording can vary, but the caption still needs to be
short and factually useful. I chose 4 out of 5 because the model may
occasionally miss a formatting instruction. Any incorrect factual detail
still counts as a failed try.

**How to check:** Read each caption against the listing and count its
sentences and mentions.

## 5. Search respects the price ceiling

Across five searches with different price ceilings, every returned listing
must have `price <= max_price` in 5 of 5 tries. Each search must include a
known matching item within budget so that returning an empty list cannot
count as passing.

**Why this target:** Budget filtering is a numeric comparison, so it should
work every time. Recommending an item above the requested limit would make
the search less useful.

**How to check:** Choose known listings from the dataset, include a case
where the ceiling equals an item's price, and inspect every returned price.

---

In unit 4, preserve these original targets. If a criterion cannot be measured,
add a dated revision and its reason underneath it. Do not lower a target merely
because a run missed it.
