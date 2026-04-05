# Reverse Chess Analysis System

Analyzes your Chess.com games from the **opponent's perspective** —
generating a "How to beat me" scouting report alongside a personal
improvement plan, all powered by Stockfish 18.

## What it does

Instead of only asking "how do I improve?", this system also asks:
**"If someone studied my games, how would they defeat me?"**

It fetches your real game history, runs every position through Stockfish,
detects patterns across openings, game length, and phases — then outputs
a dual-purpose report: a strategic playbook for opponents AND a
prioritized action plan for you.

## Sample output

ss20070315 is a tactically disciplined player who loses
positionally. Beat them with strategic pressure in the
Italian Game or Caro-Kann main line, 20-40 move middlegames.
Don't wait for a blunder — it won't come.

## Key findings (183 games analyzed)

- 91.9% of losses had zero blunders — losses are positional, not tactical
- Italian Game: 0% win rate — biggest opening gap
- Blunder rate: 0.038/game — top 10% for tactical discipline
- Strongest at 80+ moves (61% win rate), weakest at 20-40 moves (40%)

## How it works

Chess.com API → PGN Parser → Stockfish Analysis → Pattern Aggregator → Report
| Phase | Script | What it does |
|-------|--------|-------------|
| 1 | `fetch_games.py` | Fetches last N months of games via Chess.com API |
| 2 | `blunder_analysis.py` | Runs each position through Stockfish, tags blunders/mistakes |
| 3 | `build_profile.py` | Aggregates patterns — openings, length, color, errors |
| 4 | `generate_report.py` | Outputs the reverse report + improvement plan |

## Setup

### 1. Install dependencies
```bash
pip install chess requests pandas stockfish
```

### 2. Download Stockfish
Get it from [stockfishchess.org](https://stockfishchess.org/download/) and
place `stockfish.exe` in the project folder.

### 3. Set your username
Edit the `USERNAME` variable at the top of each script.

### 4. Run the pipeline
```bash
python fetch_games.py        # builds games.csv
python blunder_analysis.py   # builds blunder_analysis.csv
python build_profile.py      # prints weakness profile
python generate_report.py    # generates reverse_report.txt
```

## Tech stack

- `python-chess` — PGN parsing and board state management
- `stockfish` — Python bridge to Stockfish engine
- `requests` — Chess.com public API calls
- `pandas` — data aggregation and pattern detection

## Example weakness scores

| Metric | Score | Meaning |
|--------|-------|---------|
| Opening gap | 49.7 | Worst opening is 49.7pts below average |
| Positional losses | 91.9% | 92% of losses with zero blunders |
| Length gap | 9.7 | 9.7pt drop in worst length bucket |
| Blunder risk | 3.8% | Blunder rate per game |
