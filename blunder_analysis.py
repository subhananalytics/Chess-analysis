import requests
import chess.pgn
import chess.engine
import pandas as pd
import io
import time

USERNAME = "ss20070315"
STOCKFISH_PATH = "./stockfish.exe"
HEADERS = {"User-Agent": "chess-analyzer/1.0"}
DEPTH = 10  # balanced speed vs accuracy

def get_archives():
    url = f"https://api.chess.com/pub/player/{USERNAME}/games/archives"
    return requests.get(url, headers=HEADERS).json().get("archives", [])

def fetch_month(url):
    return requests.get(url, headers=HEADERS).json().get("games", [])

def analyze_game(pgn_text, username, engine):
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if not game:
        return None

    headers = game.headers
    is_white = headers.get("White", "").lower() == username.lower()
    board = game.board()

    blunders = mistakes = inaccuracies = 0
    phase_blunders = {"opening": 0, "middlegame": 0, "endgame": 0}
    prev_score = None
    move_num = 0

    for move in game.mainline_moves():
        move_num += 1
        is_my_turn = (board.turn == chess.WHITE) == is_white

        info = engine.analyse(board, chess.engine.Limit(depth=DEPTH))
        score = info["score"].white()

        if prev_score is not None and is_my_turn:
            try:
                prev_cp = prev_score.score(mate_score=10000)
                curr_cp = score.score(mate_score=10000)
                if prev_cp is not None and curr_cp is not None:
                    drop = (prev_cp - curr_cp) if is_white else (curr_cp - prev_cp)
                    if drop > 300:
                        blunders += 1
                        phase = "opening" if move_num <= 10 else ("middlegame" if move_num <= 30 else "endgame")
                        phase_blunders[phase] += 1
                    elif drop > 150:
                        mistakes += 1
                    elif drop > 75:
                        inaccuracies += 1
            except Exception:
                pass

        prev_score = score
        board.push(move)

    return {
        "blunders": blunders,
        "mistakes": mistakes,
        "inaccuracies": inaccuracies,
        "blunders_opening": phase_blunders["opening"],
        "blunders_middlegame": phase_blunders["middlegame"],
        "blunders_endgame": phase_blunders["endgame"],
    }

# --- Main ---
archives = get_archives()[-6:]
engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

all_rows = []
total_games = 0

for archive_url in archives:
    parts = archive_url.split("/")
    print(f"\nProcessing {parts[-2]}/{parts[-1]}...")
    games = fetch_month(archive_url)

    for g in games:
        pgn_text = g.get("pgn", "")
        if not pgn_text:
            continue

        game_obj = chess.pgn.read_game(io.StringIO(pgn_text))
        if not game_obj:
            continue

        headers = game_obj.headers
        white = headers.get("White", "")
        black = headers.get("Black", "")
        result = headers.get("Result", "*")
        is_white = white.lower() == USERNAME.lower()
        outcome = "win" if (result == "1-0" and is_white) or (result == "0-1" and not is_white) else \
                  "draw" if result == "1/2-1/2" else "loss"

        analysis = analyze_game(pgn_text, USERNAME, engine)
        if not analysis:
            continue

        analysis.update({
            "date": headers.get("Date"),
            "opening": headers.get("ECOUrl", "").split("/")[-1],
            "my_color": "white" if is_white else "black",
            "outcome": outcome,
            "moves": game_obj.end().ply(),
        })
        all_rows.append(analysis)
        total_games += 1

        if total_games % 10 == 0:
            print(f"  Analyzed {total_games} games...")

    time.sleep(0.5)

engine.quit()

df = pd.DataFrame(all_rows)
df.to_csv("blunder_analysis.csv", index=False)

print(f"\n=== RESULTS: {total_games} games analyzed ===")
print(f"Avg blunders per game:      {df['blunders'].mean():.2f}")
print(f"Avg mistakes per game:      {df['mistakes'].mean():.2f}")
print(f"Avg inaccuracies per game:  {df['inaccuracies'].mean():.2f}")
print(f"\nBlunders by phase:")
print(f"  Opening:     {df['blunders_opening'].sum()}")
print(f"  Middlegame:  {df['blunders_middlegame'].sum()}")
print(f"  Endgame:     {df['blunders_endgame'].sum()}")
print("\nSaved to blunder_analysis.csv")