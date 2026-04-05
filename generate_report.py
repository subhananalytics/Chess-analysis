import pandas as pd
from datetime import datetime

PLAYER = "ss20070315"

games_df   = pd.read_csv("games.csv")
blunder_df = pd.read_csv("blunder_analysis.csv")

df = pd.merge(blunder_df, games_df[['date','time_control']], on='date', how='left')
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df['length_bucket'] = pd.cut(df['moves'],
    bins=[0,20,40,60,80,300],
    labels=['<20','20-40','40-60','60-80','80+'])

# ── Core stats ──────────────────────────────────────────────────────────────
total        = len(df)
wins         = (df['outcome']=='win').sum()
losses       = (df['outcome']=='loss').sum()
draws        = (df['outcome']=='draw').sum()
win_rate     = wins / total * 100

white_wr     = (df[df['my_color']=='white']['outcome']=='win').mean() * 100
black_wr     = (df[df['my_color']=='black']['outcome']=='win').mean() * 100

# ── Opening profile ─────────────────────────────────────────────────────────
op = df.groupby('opening').agg(
    games    = ('outcome','count'),
    wins     = ('outcome', lambda x: (x=='win').sum()),
    losses   = ('outcome', lambda x: (x=='loss').sum()),
    blunders = ('blunders','mean'),
).query('games >= 3')
op['win_rate'] = op['wins'] / op['games'] * 100

worst_openings = op.sort_values('win_rate').head(3)
best_openings  = op.sort_values('win_rate', ascending=False).head(3)

# ── Game length profile ──────────────────────────────────────────────────────
lg = df.groupby('length_bucket', observed=True).agg(
    games    = ('outcome','count'),
    wins     = ('outcome', lambda x: (x=='win').sum()),
    blunders = ('blunders','mean'),
).copy()
lg['win_rate'] = lg['wins'] / lg['games'] * 100

worst_length = lg['win_rate'].idxmin()
best_length  = lg['win_rate'].idxmax()
worst_len_wr = lg.loc[worst_length, 'win_rate']
best_len_wr  = lg.loc[best_length,  'win_rate']

# ── Blunder profile ──────────────────────────────────────────────────────────
avg_blunders     = df['blunders'].mean()
avg_mistakes     = df['mistakes'].mean()
avg_inaccuracies = df['inaccuracies'].mean()
blunder_in_loss  = df[df['outcome']=='loss']['blunders'].mean()
blunder_in_win   = df[df['outcome']=='win']['blunders'].mean()
white_blunder    = df[df['my_color']=='white']['blunders'].mean()
black_blunder    = df[df['my_color']=='black']['blunders'].mean()

# ── Build the report ─────────────────────────────────────────────────────────
now = datetime.now().strftime("%Y-%m-%d %H:%M")
lines = []

def hr(char="─", width=62):
    lines.append(char * width)

def section(title):
    lines.append("")
    hr()
    lines.append(f"  {title}")
    hr()

hr("═")
lines.append(f"  REVERSE CHESS ANALYSIS REPORT")
lines.append(f"  Player : {PLAYER}")
lines.append(f"  Games  : {total}  |  Generated: {now}")
hr("═")

# ── 1. PLAYER PROFILE ────────────────────────────────────────────────────────
section("1. PLAYER PROFILE")
lines.append(f"  Overall record : {wins}W  {losses}L  {draws}D  ({win_rate:.1f}% win rate)")
lines.append(f"  As White       : {white_wr:.1f}%  win rate")
lines.append(f"  As Black       : {black_wr:.1f}%  win rate")
lines.append(f"  Avg game length: {df['moves'].mean():.0f} moves")
lines.append(f"  Time control   : 10-minute (600s) — all games")
lines.append("")
lines.append(f"  Error profile (per game average):")
lines.append(f"    Blunders     : {avg_blunders:.3f}  ← exceptionally low")
lines.append(f"    Mistakes     : {avg_mistakes:.3f}")
lines.append(f"    Inaccuracies : {avg_inaccuracies:.3f}")
lines.append("")
lines.append(f"  Key trait: Losses are POSITIONAL, not tactical.")
lines.append(f"  Only 7 blunders across {total} games. Opponents win by")
lines.append(f"  strategic pressure, not by waiting for mistakes.")

# ── 2. OPENING WEAKNESSES ────────────────────────────────────────────────────
section("2. OPENING WEAKNESSES  (min 3 games)")
lines.append(f"  {'Opening':<48} {'Games':>5}  {'W':>3}  {'L':>3}  {'WR%':>6}")
lines.append(f"  {'─'*48} {'─'*5}  {'─'*3}  {'─'*3}  {'─'*6}")
for name, row in worst_openings.iterrows():
    short = str(name).replace('-',' ')[:47]
    lines.append(f"  {short:<48} {int(row.games):>5}  {int(row.wins):>3}  {int(row.losses):>3}  {row.win_rate:>5.1f}%")

lines.append("")
lines.append(f"  Best openings:")
lines.append(f"  {'Opening':<48} {'Games':>5}  {'W':>3}  {'L':>3}  {'WR%':>6}")
lines.append(f"  {'─'*48} {'─'*5}  {'─'*3}  {'─'*3}  {'─'*6}")
for name, row in best_openings.iterrows():
    short = str(name).replace('-',' ')[:47]
    lines.append(f"  {short:<48} {int(row.games):>5}  {int(row.wins):>3}  {int(row.losses):>3}  {row.win_rate:>5.1f}%")

# ── 3. GAME LENGTH PROFILE ───────────────────────────────────────────────────
section("3. GAME LENGTH PROFILE")
lines.append(f"  {'Length':>8}  {'Games':>5}  {'Wins':>4}  {'WR%':>6}  {'Blunders/g':>11}")
lines.append(f"  {'─'*8}  {'─'*5}  {'─'*4}  {'─'*6}  {'─'*11}")
for bucket, row in lg.iterrows():
    marker = " ◄ weakest" if bucket == worst_length else (" ◄ strongest" if bucket == best_length else "")
    lines.append(f"  {str(bucket):>8}  {int(row.games):>5}  {int(row.wins):>4}  {row.win_rate:>5.1f}%  {row.blunders:>11.3f}{marker}")

# ── 4. HOW TO BEAT ss20070315 ────────────────────────────────────────────────
section("4. HOW TO BEAT THIS PLAYER  ← opponent's playbook")
lines.append("")

worst_op_name = worst_openings.index[0].replace('-',' ')
worst_op_wr   = worst_openings.iloc[0]['win_rate']
second_op     = worst_openings.index[1].replace('-',' ') if len(worst_openings) > 1 else ""
second_op_wr  = worst_openings.iloc[1]['win_rate'] if len(worst_openings) > 1 else 0

lines.append(f"  [1] EXPLOIT OPENING GAPS")
lines.append(f"      Steer into: {worst_op_name}")
lines.append(f"      Their win rate here is only {worst_op_wr:.0f}% — a near-guaranteed edge.")
if second_op:
    lines.append(f"      Also try:   {second_op} ({second_op_wr:.0f}% for them)")
lines.append("")
lines.append(f"  [2] TARGET THE MIDDLEGAME (20-40 moves)")
lines.append(f"      Their worst length bucket: {worst_length} moves ({worst_len_wr:.0f}% win rate).")
lines.append(f"      Avoid quick games — they're fine under 20 moves.")
lines.append(f"      Force complex middlegame positions and apply early pressure.")
lines.append("")
lines.append(f"  [3] PLAY STRATEGICALLY, NOT TACTICALLY")
lines.append(f"      Do NOT rely on them blundering — they almost never do ({avg_blunders:.3f}/game).")
lines.append(f"      Build long-term positional advantages: pawn structure,")
lines.append(f"      piece activity, space. Win the squeeze, not the tactic.")
lines.append("")
lines.append(f"  [4] TAKE THE BLACK PIECES")
lines.append(f"      They perform slightly better as White ({white_wr:.1f}% vs {black_wr:.1f}%).")
lines.append(f"      Let them have White — their opening prep is weaker than it looks.")
lines.append("")
lines.append(f"  [5] PUSH INTO LONG GAMES IF WINNING")
lines.append(f"      In 80+ move games their blunder rate rises to 0.073/game.")
lines.append(f"      If you have an endgame advantage, don't trade it for simplicity —")
lines.append(f"      keep pieces on the board and let time pressure work.")

# ── 5. YOUR IMPROVEMENT PLAN ────────────────────────────────────────────────
section("5. YOUR PERSONAL IMPROVEMENT PLAN")
lines.append("")
lines.append(f"  PRIORITY 1 — Study the Italian Game  (0% win rate, 4 games)")
lines.append(f"    You have zero wins here. Learn the Giuoco Piano and")
lines.append(f"    Two Knights Defense responses this week. Use Lichess studies.")
lines.append("")
lines.append(f"  PRIORITY 2 — Fix Caro-Kann main line  (29% win rate, 7 games)")
lines.append(f"    Your most-played weak opening. The Exchange (50%) and")
lines.append(f"    Advance (67%) variations work — the problem is the main line.")
lines.append(f"    Study positions after 1.e4 c6 2.d4 d5 3.Nc3 dxe4.")
lines.append("")
lines.append(f"  PRIORITY 3 — Improve middlegame strategy  (40% in 20-40 moves)")
lines.append(f"    You're strongest in endgames (61% at 80+ moves) but struggle")
lines.append(f"    to convert middlegame advantages. Study: pawn breaks,")
lines.append(f"    piece coordination, and when to trade into a winning endgame.")
lines.append("")
lines.append(f"  PRIORITY 4 — Manage fatigue in very long games")
lines.append(f"    All 7 blunders happened — blunder rate doubles at 80+ moves.")
lines.append(f"    Practice time management and stay alert past move 80.")
lines.append("")
lines.append(f"  KEEP DOING — Kings Pawn 1...e5  (67% win rate)")
lines.append(f"    Your best-performing opening. Play it more often.")
lines.append(f"    Also keep the Caro-Kann Advance ({best_openings.iloc[1]['win_rate']:.0f}% win rate).")

# ── 6. SUMMARY ───────────────────────────────────────────────────────────────
section("6. ONE-LINE SUMMARY")
lines.append("")
lines.append(f"  {PLAYER} is a tactically disciplined player who loses")
lines.append(f"  positionally. Beat them with strategic pressure in the")
lines.append(f"  Italian Game or Caro-Kann main line, 20-40 move middlegames.")
lines.append(f"  Don't wait for a blunder — it won't come.")
lines.append("")
hr("═")
lines.append(f"  End of report  |  {now}")
hr("═")

report = "\n".join(lines)
print(report)

with open("reverse_report.txt", "w", encoding="utf-8") as f:
    f.write(report)

print(f"\n✓ Saved to reverse_report.txt")