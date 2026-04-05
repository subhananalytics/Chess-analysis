import requests
import chess.pgn
import pandas as pd
import io
import time

USERNAME = "ss20070315"
HEADERS = {"User-Agent": "chess-analyzer/1.0"}

def get_available_archives():
    url = f"https://api.chess.com/pub/player/{USERNAME}/games/archives"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("archives", [])

def fetch_games_for_month(archive_url):
    response = requests.get(archive_url, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("games", [])

def parse_game(game_data):
    pgn_text = game_data.get("pgn", "")
    if not pgn_text:
        return None

    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if not game:
        return None

    headers = game.headers
    white  = headers.get("White", "")
    black  = headers.get("Black", "")
    result = headers.get("Result", "*")
    moves  = game.end().ply()

    if white.lower() == USERNAME.lower():
        color = "white"
        outcome = "win" if result == "1-0" else ("draw" if result == "1/2-1/2" else "loss")
    else:
        color = "black"
        outcome = "win" if result == "0-1" else ("draw" if result == "1/2-1/2" else "loss")

    return {
        "date":         headers.get("Date", ""),
        "white":        white,
        "black":        black,
        "result":       result,
        "my_color":     color,
        "outcome":      outcome,
        "opening":      headers.get("ECOUrl", "Unknown").split("/")[-1],
        "eco":          headers.get("ECO", ""),
        "moves":        moves,
        "time_control": game_data.get("time_control", ""),
    }

def fetch_all_games(months_back=6):
    archives = get_available_archives()
    archives = archives[-months_back:]  # last N months

    all_rows = []
    for archive_url in archives:
        parts = archive_url.split("/")
        year, month = parts[-2], parts[-1]
        print(f"Fetching {year}/{month}...", end=" ", flush=True)

        games = fetch_games_for_month(archive_url)
        print(f"{len(games)} games")

        for g in games:
            row = parse_game(g)
            if row:
                all_rows.append(row)

        time.sleep(0.5)

    df = pd.DataFrame(all_rows)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)
    return df

# --- Run ---
df = fetch_all_games(months_back=6)

print(f"\nTotal games: {len(df)}")
print(f"Date range:  {df['date'].min().date()} → {df['date'].max().date()}")
print(f"\nOutcome breakdown:\n{df['outcome'].value_counts()}")
print(f"\nTop 5 openings:\n{df['opening'].value_counts().head()}")

df.to_csv("games.csv", index=False)
print("\nSaved to games.csv")