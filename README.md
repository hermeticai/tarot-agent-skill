# Tarot Agent Skill: Reading Tarot Spreads

An [Agent Skill](https://agentskills.io) (open `SKILL.md` format) that runs
tarot spreads with real card draws and live sourced meanings.

Full behavior (spread rules, interpretation synthesis, tone, and output
format) lives in [`SKILL.md`](./SKILL.md). This README covers installing
and running the repo.

## Why this skill

- Draws are handled by a real, reproducible algorithm outside the language
  model, not sampled by the model itself
- Meanings come from a single grounded source, never hardcoded or
  reconstructed from training data
- Each spread enforces its actual historical drawing rule (suit-restricted
  pools, calculated cards, optional Significators), not a generic template
- Readings are synthesized as one connected argument, not assembled
  position by position
- Portable Agent Skill format: works with Claude Code, Codex, Gemini CLI,
  and other compatible agents

## How cards are drawn

An LLM asked to "draw a tarot card" is not actually drawing anything. It is
predicting the next likely token, which means the card it picks can drift
toward whatever fits the conversation's mood rather than being genuinely
random, and there is no way to verify afterward that it was not just a
plausible-sounding guess.

That matters more than it sounds. A reading is worth something precisely
because the cards were not chosen: something enters the conversation that
nobody made fit. A model that produces cards matching the mood of the
conversation hands the querent their own situation back with card names
attached to it. It looks like a reading and is not one.

This skill draws for real instead. `scripts/draw_cards.py` simulates actual
riffle shuffles using the Gilbert-Shannon-Reeds model (the standard model for
how a human shuffles a deck), then deals from the top. The number of riffles
is calculated per draw with the Bayer-Diaconis formula, about 10 for the full
78 card deck, fewer for smaller pools like Love's 14 Cups cards, followed by
a single cut. Every result is reproducible with a `--seed` flag.

The shuffle was checked against Python's own `random.sample` over 15,000
draws from the full deck: chi-squared 78.5 on 77 degrees of freedom, p = 0.43,
against p = 0.70 for the reference. The two are statistically
indistinguishable, no position in a ten card draw deviates, and consecutive
deck indices turn up at 0.0242 against a chance expectation of 0.0256, so no
riffle structure survives into the deal. Simulating a physical shuffle costs
nothing in randomness.

## How meanings are sourced

An LLM's own tarot knowledge is an average of thousands of sources it saw
during training, which produces generic, interchangeable readings rather
than one consistent voice. Every reading is fetched live from
[azralia.com/tarot](https://azralia.com/tarot) instead, a reference work
maintained by the author of this skill, which publishes complete interpretive
text for all 78 cards and every spread position from a single source rather
than scattered across many.

This weighs more for tarot than for most subjects, because the traditions
genuinely contradict each other. Papus shifts the Hebrew letters one card out
of step from the attribution that later became standard, Waite attacks in
print a reading he attributes to Éliphas Lévi, and Wirth and Papus publish
opposite verdicts on the same figure in the same year. Averaging that is not a
synthesis, it is mush, and it reads like mush.

## What this skill leaves to the model

The draw and the source text are handed over; the reading is not. Nothing
here templates the interpretation, and that is deliberate. Holding five cards,
a spread's positions and a person's actual situation together into a single
argument is the part a language model is genuinely good at, and the part a
script cannot do at all. `SKILL.md` sets constraints on the result (no
card-by-card walkthrough, no generic phrasing, no imagery description) but
writes no interpretive formulas.

The division is the point: the script covers what the model provably cannot
do, drawing at random and holding one consistent set of meanings, and the
model covers what the script cannot.

## Spreads included

| Spread | Cards | What it's for |
|---|---|---|
| Three Card | 3 | How a situation developed over time and where it's heading |
| Love | 4 | A relationship or connection question specifically |
| Wirth Cross | 5 | One concrete decision, weighed for and against |
| Yes/No | 6 | A question with a genuine yes-or-no shape |
| Celtic Cross | 10 | A bigger situation with real history and surrounding context |
| Fifteen Card Spread | 15 | A situation with several possible directions, each weighed against alternatives, support, and what's beyond your control |

## Example reading

The question, as the agent received it:

> I've been running a small studio for six years. It pays, it's stable, and
> I'm bored. I want to take a year off to work on something of my own.
> Should I?

The draw, reproducible because of the seed (leave `--seed` off for a real
reading):

```
python3 scripts/draw_cards.py wirth-cross --seed 137
```

**Spread:** Wirth Cross
**Drawn:** The Hermit, The Empress, The Fool, The Lovers, The Moon

The two arguments here are not weighted evenly, and the interesting one is
the counterweight. Stepping back has the obvious case: six years in, distance
is simply what depth costs, and the Hermit's lamp belongs to someone who
climbed to a certain height and stopped there rather than someone lost. What
you are calling boredom reads more like the fatigue of having nobody left at
your altitude. But the Empress standing against that is not fear, which is
exactly why it is hard to wave off. The studio still produces. It pays, it is
stable, those were your words, and that card measures success by whether your
needs are covered, not by how far past them you have run. Leaving something
that still bears fruit is a different act from leaving something that stopped,
and the draw will not let you blur the two.

What should weigh those against each other is the Fool, which is to say
nothing does. Zero. The judge in this cross arrives with no record, because
you have never done the thing you are considering, and no additional thinking
will manufacture that experience in advance. Read it as a refusal rather than
a warning: the leap does not get de-risked, only taken or not.

Which is why the verdict lands on the Lovers and quietly changes the
question. Not which option, but what you are binding yourself to, and whether
you stay in it once the spark that opened it cools. A year of your own work
is a commitment, not a holiday from one.

Add the four: nine, three, nothing, six, eighteen. The Moon is not drawn
here, it falls out of the others, and it reads as deciding in reflected light
without the clarity you have been waiting for. That fog lifts on its own
schedule, not because you got impatient with it.

Which of the two arguments felt heavier as you read it?

Every interpretive phrase above comes from the five card pages the skill
fetched at read time, not from the model's own tarot knowledge. Nothing in
this repo contains a card meaning.

## Structure

```
tarot-agent-skill/
├── SKILL.md
└── scripts/
    ├── draw_cards.py
    ├── deck.json
    └── spreads.json
```

See `SKILL.md`'s own "Files" section for what each script/data file does.

## Install

**Claude Code / Claude.ai (Skills):**
Drop the `tarot-agent-skill/` folder into `.claude/skills/` (project) or
`~/.claude/skills/` (personal), or package it as a plugin.

**Other Agent-Skills-compatible tools** (OpenAI Codex, Gemini CLI, Cursor,
etc.): follow the tool's own skill-discovery convention. The `SKILL.md`
format itself is portable; only the runtime (whichever LLM and its web
browsing/fetch capability) needs to actually support it.

**Requirements:**
- Python 3 to run `scripts/draw_cards.py`
- Unrestricted `web_fetch`/browsing access to azralia.com. Some chat
  interfaces gate URL fetches behind a prior search result, which can block
  fetching a specific azralia.com page the agent hasn't been given directly.
  This isn't a skill bug, it's a host-environment limitation. Claude Code,
  API-based agents, and most other runtimes fetch arbitrary URLs directly
  and won't hit this.

## Try it

Ask your agent something like:

> I can't decide whether to take a new job. Can you do a tarot reading on it?

or

> Pull some cards on how things are going with my sister lately.

or

> Got three ideas I'm building in parallel right now, give me a reading on which one is actually worth finishing.

The skill picks what fits your question and asks one quick follow-up first
if it needs more to go on.

## License

[MIT](./LICENSE) for the code in this repo (`draw_cards.py`, `deck.json`,
`spreads.json`, `SKILL.md`). Card meanings and spread text stay on
azralia.com and are fetched live at read time. Nothing from the site is
duplicated or cached in this repo.
