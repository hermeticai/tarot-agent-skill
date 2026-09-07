#!/usr/bin/env python3
"""
Draws cards for one of the six supported spreads and prints a JSON result
mapping each spread position to a drawn card and the page URL where its
meaning should be looked up (via web_fetch by the caller).

This script does NOT know any card meanings. It only knows card names,
positions, and which azralia.com page holds the meaning for each card.
That page is fetched live by the calling agent so the reading always
reflects the current published text.

SHUFFLING: cards are not sampled with random.sample() (which is a
statistically "perfect" but physically unrealistic draw). Instead this
script simulates real riffle shuffles using the Gilbert-Shannon-Reeds (GSR)
model, the standard mathematical model for how a human actually shuffles
a deck (Gilbert & Shannon 1955, Reeds 1981), plus an optional single cut,
then deals from the top like a real dealer would. See --riffles and --cut.

Usage:
    python3 draw_cards.py <spread-slug> [--seed N] [--riffles N] [--no-cut]

Spread slugs: three-card, love, wirth-cross, yes-no, celtic-cross, fifteen-card
"""
import json
import math
import random
import argparse
from pathlib import Path

HERE = Path(__file__).parent


def load_json(name):
    with open(HERE / name, encoding="utf-8") as f:
        return json.load(f)


def build_full_deck(deck):
    """Return list of card dicts: {name, page_url, arcana, suit, number}"""
    cards = []
    url_pattern = deck["major_arcana"]["url_pattern"]
    for c in deck["major_arcana"]["cards"]:
        cards.append({
            "name": c["name"],
            "number": c["number"],
            "arcana": "major",
            "suit": None,
            "page_url": url_pattern.format(slug=c["slug"]),
        })
    for suit, info in deck["minor_arcana"]["suits"].items():
        for rank in deck["minor_arcana"]["ranks"]:
            name = f"{rank} of {suit.capitalize()}"
            cards.append({
                "name": name,
                "number": rank,
                "arcana": "minor",
                "suit": suit,
                "page_url": info["page_url"],
            })
    return cards


def cards_for_rule(rule, deck):
    full = build_full_deck(deck)
    if rule == "full_deck":
        return full
    if rule == "suit:cups":
        return [c for c in full if c["suit"] == "cups"]
    if rule == "major_arcana_plus_calculated":
        return [c for c in full if c["arcana"] == "major"]
    raise ValueError(f"Unknown draw_rule: {rule}")


def reduce_to_card_number(total, max_number=21):
    """Digit-sum reduction until the result is <= max_number (Wirth Cross rule)."""
    while total > max_number:
        total = sum(int(d) for d in str(total))
    return total


# ---------------------------------------------------------------------------
# Gilbert-Shannon-Reeds riffle shuffle
# ---------------------------------------------------------------------------

def recommended_riffles(n):
    """
    Bayer & Diaconis (1992): (3/2)*log2(n) riffle shuffles are necessary and
    sufficient to randomize a deck of n cards (the classic "7 shuffles"
    result is this formula evaluated at n=52). For n=78 that comes out to
    roughly 10; smaller pools (e.g. the 14-card Cups-only Love spread) need
    fewer.
    """
    if n <= 1:
        return 0
    return max(1, math.ceil(1.5 * math.log2(n)))


def gsr_riffle(deck, rng):
    """
    One Gilbert-Shannon-Reeds riffle shuffle:
      1. Cut the deck into two piles at a binomially-distributed position
         (not an exact half; a real cut is uneven).
      2. Interleave the two piles by dropping the next card from whichever
         pile, with probability proportional to that pile's remaining size
         (not a fixed 50/50 coin flip per card; bigger piles are more
         likely to contribute the next card, matching how a real riffle's
         "streaks" of consecutive same-pile cards actually behave).
    """
    n = len(deck)
    # Binomial(n, 0.5) cut position, sampled as n independent coin flips.
    k = sum(1 for _ in range(n) if rng.random() < 0.5)
    pile_a, pile_b = deck[:k], deck[k:]

    result = []
    ia, ib = 0, 0
    a_left, b_left = len(pile_a), len(pile_b)
    while ia < len(pile_a) and ib < len(pile_b):
        if rng.random() < a_left / (a_left + b_left):
            result.append(pile_a[ia])
            ia += 1
        else:
            result.append(pile_b[ib])
            ib += 1
        a_left, b_left = len(pile_a) - ia, len(pile_b) - ib
    result.extend(pile_a[ia:])
    result.extend(pile_b[ib:])
    return result


def shuffle_deck(deck, rng, riffles):
    d = list(deck)
    for _ in range(riffles):
        d = gsr_riffle(d, rng)
    return d


def cut_deck(deck, rng):
    """A single cut: split at a random point and swap the two halves."""
    n = len(deck)
    if n < 2:
        return list(deck)
    k = rng.randint(1, n - 1)
    return deck[k:] + deck[:k]


def shuffle_and_deal(pool, n_needed, rng, riffles=None, do_cut=True):
    """Shuffle `pool` with real GSR riffles, optionally cut, then deal the
    top n_needed cards like a real dealer would. Returns (dealt, meta)."""
    riffle_count = recommended_riffles(len(pool)) if riffles is None else riffles
    shuffled = shuffle_deck(pool, rng, riffle_count)
    if do_cut:
        shuffled = cut_deck(shuffled, rng)
    dealt = shuffled[:n_needed]
    meta = {"pool_size": len(pool), "riffles": riffle_count, "cut": do_cut}
    return dealt, meta


# ---------------------------------------------------------------------------

def draw(spread_slug, seed=None, riffles=None, do_cut=True):
    deck = load_json("deck.json")
    spreads = load_json("spreads.json")["spreads"]

    if spread_slug not in spreads:
        raise SystemExit(
            f"Unknown spread '{spread_slug}'. Choices: {', '.join(spreads)}"
        )

    spread = spreads[spread_slug]
    rng = random.Random(seed)

    pool = cards_for_rule(spread["draw_rule"], deck)
    shuffle_meta = None

    if spread["draw_rule"] == "major_arcana_plus_calculated":
        # Shuffle & deal 4 real Major Arcana cards; the 5th is calculated.
        drawn, shuffle_meta = shuffle_and_deal(pool, 4, rng, riffles, do_cut)
        total = sum(c["number"] for c in drawn)
        fifth_number = reduce_to_card_number(total)
        fifth_card = next(c for c in deck["major_arcana"]["cards"]
                           if c["number"] == fifth_number)
        fifth = {
            "name": fifth_card["name"],
            "number": fifth_card["number"],
            "arcana": "major",
            "suit": None,
            "page_url": deck["major_arcana"]["url_pattern"].format(slug=fifth_card["slug"]),
            "calculated": True,
            "calculation": f"{' + '.join(str(c['number']) for c in drawn)} = {total}"
                            + (f" -> reduced to {fifth_number}" if total > 21 else ""),
        }
        drawn = drawn + [fifth]
    else:
        n = spread["card_count"]
        if n > len(pool):
            raise SystemExit(
                f"Spread needs {n} cards but only {len(pool)} are available in this pool."
            )
        drawn, shuffle_meta = shuffle_and_deal(pool, n, rng, riffles, do_cut)

    positions = spread["positions"]
    result = {
        "spread": spread_slug,
        "display_name": spread["display_name"],
        "source_page": "https://azralia.com/tarot/spreads/",
        "special_instructions": spread.get("special_instructions"),
        "shuffle": shuffle_meta,
        "draws": [],
    }
    for i, pos_name in enumerate(positions):
        card = drawn[i]
        entry = {
            "position": i + 1,
            "position_name": pos_name,
            "card": card["name"],
            "meaning_page_url": card["page_url"],
        }
        if card.get("calculated"):
            entry["calculated"] = True
            entry["calculation"] = card["calculation"]
        result["draws"].append(entry)

    result["pages_to_fetch"] = sorted({d["meaning_page_url"] for d in result["draws"]})

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("spread", help="Spread slug, e.g. three-card, celtic-cross")
    parser.add_argument("--seed", type=int, default=None, help="Optional RNG seed")
    parser.add_argument("--riffles", type=int, default=None,
                         help="Override number of GSR riffle shuffles "
                              "(default: (3/2)*log2(pool size), rounded up)")
    parser.add_argument("--no-cut", action="store_true",
                         help="Skip the single cut after shuffling")
    args = parser.parse_args()

    result = draw(args.spread, seed=args.seed, riffles=args.riffles,
                  do_cut=not args.no_cut)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
