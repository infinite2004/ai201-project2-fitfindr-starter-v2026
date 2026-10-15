"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re
import trace
from tools import (
    search_listings, suggest_outfit, create_fit_card,
    NO_ITEM_OUTFIT, NO_OUTFIT_RESPONSE, NO_OUTFIT, NO_ITEM_CARD, NO_CARD_RESPONSE,
)
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── query parsing and planning loop ──────────────────────────────────────────

_PRICE = re.compile(
    r"\b(?:under|below|up\s+to|max(?:imum)?)\s*\$?\s*"
    r"(-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)(?![\d.])",
    re.IGNORECASE,
)
_CLOTHING_SIZE = r"(?:XXXL|XXL|XXXS|XXS|XL|XS|S|M|L|[2-6]XL)"
_SIZE = re.compile(
    r"\bsize\s+("
    r"one\s+size|"
    r"w\d+(?:\s+l\d+)?|"
    r"(?:us\s*)?\d+(?:\.\d+)?|"
    + _CLOTHING_SIZE + r"(?:\s*/\s*" + _CLOTHING_SIZE + r")*"
    r")(?![a-z0-9./])(?:\s*\([^)]*\))?",
    re.IGNORECASE,
)


def parse_query(query: str) -> dict:
    """Extract common size/price phrases; keep remaining words for search."""
    description = query.strip()
    price_match = _PRICE.search(description)
    max_price = float(price_match[1].replace(',', '')) if price_match else None
    if price_match:
        description = description[:price_match.start()] + ' ' + description[price_match.end():]
    size_match = _SIZE.search(description)
    size = size_match[1].strip() if size_match else None
    if size_match:
        description = description[:size_match.start()] + ' ' + description[size_match.end():]
    description = ' '.join(description.replace(',', ' ').split())
    return {'description': description, 'size': size, 'max_price': max_price}


def run_agent(query: str, wardrobe: dict) -> dict:
    """Run the branching tool loop; persist results before calling each tool.

    Empty searches stop immediately. Missing model output and connection
    failures also set error rather than masquerading as successful fit cards.
    """
    session = new_session(query, wardrobe)
    session['parsed'] = parse_query(session['query'])
    try:
        for count, stage in enumerate(('search', 'outfit', 'card'), start=1):
            trace.check_iterations(count)
            if stage == 'search':
                session['search_results'] = search_listings(**session['parsed'])
                if not session['search_results']:
                    session['error'] = (
                        'No listings matched your search. Try broader description '
                        'keywords, a different size, or a higher price limit.'
                    )
                    return session
                session['selected_item'] = session['search_results'][0]
            elif stage == 'outfit':
                session['outfit_suggestion'] = suggest_outfit(
                    session['selected_item'], session['wardrobe']
                )
                if (not session['outfit_suggestion'].strip()
                        or session['outfit_suggestion'] in (NO_ITEM_OUTFIT, NO_OUTFIT_RESPONSE)):
                    session['error'] = session['outfit_suggestion'] or NO_OUTFIT_RESPONSE
                    return session
            else:
                session['fit_card'] = create_fit_card(
                    session['outfit_suggestion'], session['selected_item']
                )
                if (not session['fit_card'].strip()
                        or session['fit_card'] in (NO_OUTFIT, NO_ITEM_CARD, NO_CARD_RESPONSE)):
                    session['error'] = session['fit_card'] or NO_CARD_RESPONSE
    except ModelUnavailable:
        session['error'] = (
            'The model is unavailable. Check your API key, model setting, and '
            'internet connection, then try again.'
        )
    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
