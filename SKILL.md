---
name: reading-tarot-spreads
description: Perform a tarot reading using six spreads and card meanings fetched live from azralia.com/tarot. Use when the user asks for a tarot reading, a card spread, wants to "draw cards", mentions a specific spread by name (Three Card, Love, Wirth Cross, Yes/No, Celtic Cross, Fifteen Card Spread), or asks a question they'd like the cards' input on. Do NOT use for general tarot trivia questions that don't involve an actual reading.
---

# Reading Tarot Spreads

Runs a tarot reading using the six spreads at https://azralia.com/tarot/spreads/
and the card meanings across https://azralia.com/tarot/ (Major Arcana) and the
four suit pages (Wands, Cups, Swords, Pentacles). No card or position meaning
is hardcoded here, only names and URLs. Every interpretive word is fetched
live, so a reading always reflects whatever is currently published.

## Workflow

0. **Understand the question before drawing.** Don't draw off a one-line
   request. If it's underspecified, ask one clarifying question first, about
   what's at stake or what they're hoping to find out. Skip only for
   low-stakes pulls (a plain "card of the day").

1. **Pick a spread.** If named, use it. Otherwise offer the six and suggest
   one based on the question: Three Card (general/quick), Love (relationship),
   Wirth Cross (one concrete decision), Yes/No (yes-or-no shape), Celtic Cross
   (a bigger situation with history), Fifteen Card Spread (Celtic Cross
   alternative, more combinatorial).

   Slugs (internal identifiers for the script, not azralia.com URLs):
   `three-card`, `love`, `wirth-cross`, `yes-no`, `celtic-cross`,
   `fifteen-card`.

2. **Fetch the spread's position meanings.** `web_fetch`
   https://azralia.com/tarot/spreads/ once. Covers all six spreads' position
   meanings and "About this spread" context. Read the chosen spread's section.

3. **Draw the cards.** Run:
   ```
   python3 scripts/draw_cards.py <spread-slug>
   ```
   Returns JSON: card per position, plus `pages_to_fetch`. Cards aren't
   sampled with `random.sample`; the script simulates real riffle shuffles
   (Gilbert-Shannon-Reeds model: uneven binomial cut, piles interleaved
   weighted by remaining size), the mathematically-derived riffle count for a
   well-mixed deck of that size (about 10 for 78 cards, fewer for smaller
   pools), then a cut, then deals from the top. The `shuffle` field reports
   pool size, riffle count, and whether a cut happened. Per-spread rules the
   script already enforces:
   - Love draws only from the 14 Cups cards.
   - Wirth Cross draws 4 Major Arcana and calculates the 5th (Synthesis) by
     summing the others' numbers, digit-reducing to 22-or-under. See the
     `calculation` field.
   - Celtic Cross's Significator (11th "card") is chosen, not drawn, and not
     itself interpreted. Only offer it if the user wants one.
   - All other spreads draw from the full 78-card deck.

4. **Fetch each drawn card's meaning.** `web_fetch` every URL in
   `pages_to_fetch`. Minor Arcana share one suit page per suit (dedupe
   repeats); Major Arcana each have their own page
   (`azralia.com/tarot/<slug>/`, article "the" dropped from the slug, e.g.
   `/fool/`, `/wheel-of-fortune/`). Every page gives the full meaning, an
   image description, and (Minor) Sephira/element or (Major) planet/sign,
   Hebrew letter, Tree-of-Life path.

5. **Present the reading.** Before writing anything, work out the whole
   reading as one problem: question, all cards, and positions held together
   to find the actual throughline: which cards carry the real weight, how
   they argue with or reinforce each other. This synthesis happens before any
   output is written, not by drafting positions in sequence and summarizing
   after.

   Scan the draw as a set: repeated suits/numbers, court vs. number cards,
   Major-to-Minor ratio, any repeat across a Wirth Cross calculation.

   As part of the same silent synthesis, cross-reference each card's
   Qabalistic placement (stated on its page: Tree-of-Life path for Major
   Arcana, single Sephira for Minor) against your own broader Qabalistic
   knowledge: shared Sephirot, adjacent paths, a cluster in one Pillar or
   World. This is real analysis that should shape the throughline.
   **It never surfaces in the visible reading.** No Sephirot, Hebrew
   letters, or Tree-of-Life language in the output, ever, regardless of how
   much it shaped the synthesis.

   Write the throughline as prose (see Output format), not position by
   position:
   - Applied, not descriptive: what a card means *here*, not what it depicts.
     No imagery, no picture description, no symbolism tangent.
   - **Fuse with the person's actual specifics.** "The opposing force here
     is..." restates a card's generic meaning with a label attached, not an
     interpretation yet. Use the concrete details the person gave. If step 0
     didn't surface enough, go back and ask rather than filling the gap with
     generic phrasing.
   - Not every card needs its own sentence. Weight by what's load-bearing
     for the throughline, not by spread-completeness.
   - Wirth Cross's calculated 5th card: work the arithmetic into the prose,
     don't set it off separately.

   Don't end on a flat close. Invite a real reaction (what lands, what feels
   off), the way an in-person reader keeps the conversation open rather than
   delivering a verdict and moving on.

   A published HTML page (via the Artifact tool) works well if the user wants
   something visual or shareable. Lay cards out in the spread's actual
   geometry, link each back to its source page.

## Reading craft

- **One committed voice, not a hedged one.** Once the reading starts, stay in
  the practice: state what the cards say plainly (the Yes/No spread has a
  position literally called "The Answer"; honor that). Don't break voice
  position-by-position with meta-commentary about what tarot can or can't
  know, and don't add a framing disclaimer before or after either.
- **Let the language carry the honesty.** "The cards suggest", "this points
  to", "reads as": already accurate, reports what the draw indicates without
  claiming a specific future fact. Stay in this phrasing rather than
  switching to flatly declarative claims about what will happen.
- **Never claim certainty about a specific real person's future action.**
  Phrase it as what the cards indicate, not "she will..." as fact. That's the
  one line to hold; everything else stays fully in voice.

## Tone

Literary and specific, not generic fortune-cookie phrasing. Card meanings are
a lens for reflection, not a fixed prediction. No absolute claims about the
future, no firm guidance on health, legal, or financial decisions (defer
those to the user's own judgment or a professional).

## Output format

- **Two labeled meta lines, no per-card list:**
  ```
  **Spread:** <display name>
  **Drawn:** <Card 1>, <Card 2>, <Card 3>, ...
  ```
  Card names only, no positions, no meanings. A bare reference line, not
  part of the interpretation.
- **The reading itself is flowing prose, not a list.** One paragraph per
  position is wrong. Cards get named in passing, in service of a point, not
  as the organizing skeleton. A reader should come away with an argument
  about their situation, not a ten-card walkthrough. The Qabalah
  cross-referencing from step 5 stays invisible here too.
- **No inline card images.** Plain external image links show as a
  click-through card in most chat clients, not a picture. Only include if
  explicitly asked (see `image_search`), never by default.
- **End on an open note.** No flat restatement of the outcome as the last
  sentence.
- **Length scales with card count, not detail available.** Even at 15
  cards, read like focused thinking, not a card-by-card ledger.

## Files

- `scripts/draw_cards.py`: draws cards, returns pages to fetch. Run it,
  don't reimplement inline.
- `scripts/deck.json`: 78 card names plus source page per card. Structural
  only, no meanings.
- `scripts/spreads.json`: draw rules plus position order per spread.
  Position meanings intentionally not duplicated; always fetched live.
