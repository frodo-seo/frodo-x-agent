# Nagne X Bot — Project Guide for Claude

## What this is
Automated X account that posts 1 daily Korean-language news summary focused on **US stocks and crypto**. Targets Korean retail investors (서학개미·코인러) who want market-moving news before the day starts. Runs via GitHub Actions at 7AM KST daily.

## Stack
- **LLM:** Claude Sonnet via `anthropic` — `ANTHROPIC_API_KEY`
- **Search/Research:** Tavily — `TAVILY_API_KEY`
- **Trend discovery:** Google News RSS via `feedparser` (zero API credits)
- **Posting:** X API via `tweepy` OAuth 1.0a — 4 keys required
- **Automation:** GitHub Actions cron `0 22 * * *` (= 07:00 KST)

## Pipeline flow
```
Google News RSS → Curator (LLM) → per topic:
    Researcher → Writer → Validator + Editor (loop, max 2 revisions)
    → FactChecker (Tavily) → post or skip
```
- Curator selects `n × 4` candidates to absorb fact-check failures
- Both **contradicted** and **unverified** claims block posting
- 5-day dedup via `posts_log.jsonl` (gitignored, not persisted across Actions runs)

## Key files
| File | Purpose |
|------|---------|
| `src/frodo/persona.py` | Nagne persona prompt — tune tone here |
| `src/frodo/agents/curator.py` | Topic selection with dedup injection |
| `src/frodo/agents/researcher.py` | Extracts structured NewsBrief from search results |
| `src/frodo/agents/writer.py` | Drafts X post (115 char text limit) |
| `src/frodo/agents/editor.py` | Tone, hedge, Korean angle, factual grounding check |
| `src/frodo/agents/factchecker.py` | Tavily-verifies 2-3 claims; blocks if any fail |
| `src/frodo/pipeline.py` | Orchestration — `draft_brief()` is the main entry |
| `src/frodo/validators.py` | Deterministic checks: weighted length, emoji, hashtags |
| `src/frodo/post_log.py` | Append-only JSONL dedup log |
| `.github/workflows/nagne.yml` | GitHub Actions daily cron |

## Persona rules (Nagne / 나그네)
- Casual Korean X-native tone: ㅋㅋ/ㄹㅇ/진짜 allowed
- No emoji, no hashtags, no rhetorical questions
- Always link Korean angle (semis/autos/FX/North Korea/China/trade/energy)
- Cite US outlet in text
- 115 Korean chars max for text body (URL auto-appended = 23 weighted chars via t.co)
- Declarative endings only

## Character counting
Korean characters count as 2 weighted chars. URLs normalized to 23 chars (t.co). See `validators.py:x_weighted_length()`.

## Running locally
```bash
pip install -r requirements.txt
cp .env.example .env  # fill in keys

# dry run (no post)
python -m src.frodo.main brief -n 3

# with posting
python -m src.frodo.main brief -n 3 --post

# single topic
python -m src.frodo.main draft "US tariff Korea"
```

## Environment variables
```
ANTHROPIC_API_KEY   # Anthropic API
TAVILY_API_KEY      # Tavily search
X_API_KEY           # X OAuth 1.0a
X_API_SECRET
X_ACCESS_TOKEN
X_ACCESS_TOKEN_SECRET
MODEL_ID            # optional, defaults to claude-sonnet-4-6
```

## GitHub Actions secrets
6 individual Repository secrets required (Settings → Secrets and variables → Actions). `MODEL_ID` secret not needed — default is hardcoded in `config.py`.

## Known limitations / future ideas
- `posts_log.jsonl` resets each Actions run (dedup only works within a session)
- Reddit API integration for trend signal (blocked during initial build)
- Upgraded to Claude Sonnet from Gemini Flash Lite
