# Nagne (나그네) — US News for Korean Readers

Automated X bot that posts daily Korean-language news summaries sourced from US media. Built for Korean morning readers who want US/global news with Korean context.

Posts 3 stories daily at 7AM KST via GitHub Actions.

## How it works

```
Google News RSS → Curator → per topic:
    Tavily Search → Researcher → Writer → Validator + Editor (max 2 revisions)
    → Fact-Checker → Post or Skip
```

- **Curator** picks the most Korea-relevant stories from ~50 RSS headlines
- **Researcher** extracts structured facts from Tavily deep search results
- **Writer** drafts a post in Nagne's casual Korean voice (115 char limit)
- **Editor** (LLM) + **Validator** (deterministic) catch tone/fact/format issues and loop back
- **Fact-Checker** verifies claims via Tavily; contradicted claims block posting
- Buffer strategy: selects `n x 4` candidates to absorb failures

## Persona

Nagne is an X-native Korean voice — casual, opinionated, concise. Think "texting a smart friend about the news."

- Casual Korean (ㅋㅋ, ㄹㅇ, 진짜)
- No emoji, no hashtags, no rhetorical questions
- Always links to Korean angle (semis, autos, FX, North Korea, China, trade, energy)
- Cites US outlet in text
- 115 Korean chars max, declarative endings only

## Stack

| Layer | Tool |
|-------|------|
| LLM | Claude Sonnet via Anthropic API |
| Search | Tavily (deep search + fact-check) |
| Headlines | Google News RSS (zero cost) |
| Posting | X API via tweepy (OAuth 1.0a) |
| Automation | GitHub Actions cron |

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # fill in your keys
```

### Environment variables

```
ANTHROPIC_API_KEY     # Anthropic API
TAVILY_API_KEY        # Tavily search
X_API_KEY             # X OAuth 1.0a
X_API_SECRET
X_ACCESS_TOKEN
X_ACCESS_TOKEN_SECRET
MODEL_ID              # optional (default: claude-sonnet-4-6)
```

## Usage

```bash
# dry run — discover top stories, draft posts, don't publish
python -m src.frodo.main brief -n 3

# publish to X
python -m src.frodo.main brief -n 3 --post

# single topic
python -m src.frodo.main draft "US tariff Korea"

# force past dedup check
python -m src.frodo.main draft "US tariff Korea" --force
```

## GitHub Actions

Runs daily at `0 22 * * *` UTC (= 07:00 KST). Requires 6 repository secrets:

`ANTHROPIC_API_KEY`, `TAVILY_API_KEY`, `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`

## License

See [LICENSE](LICENSE).
