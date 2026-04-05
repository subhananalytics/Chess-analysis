import pandas as pd

PLAYER = "ss20070315"

# Load both files you already have
games_df   = pd.read_csv("games.csv")
blunder_df = pd.read_csv("blunder_analysis.csv")

# Merge them together on date
df = pd.merge(blunder_df, games_df[['date', 'time_control']], on='date', how='left')
df['date'] = pd.to_datetime(df['date'], errors='coerce')

def build_profile(df):
    profile = {}

    # ── Win rate by opening (min 3 games) ───────────────────────────────────
    op = df.groupby('opening').agg(
        games    = ('outcome', 'count'),
        wins     = ('outcome', lambda x: (x == 'win').sum()),
        losses   = ('outcome', lambda x: (x == 'loss').sum()),
        blunders = ('blunders', 'mean'),
    ).query('games >= 3')
    op['win_rate'] = (op['wins'] / op['games'] * 100).round(1)
    profile['opening'] = op.sort_values('win_rate')

    # ── Win rate by game length ──────────────────────────────────────────────
    df['length_bucket'] = pd.cut(
        df['moves'],
        bins=[0, 20, 40, 60, 80, 300],
        labels=['<20', '20-40', '40-60', '60-80', '80+']
    )
    lg = df.groupby('length_bucket', observed=True).agg(
        games    = ('outcome', 'count'),
        wins     = ('outcome', lambda x: (x == 'win').sum()),
        blunders = ('blunders', 'mean'),
    )
    lg['win_rate'] = (lg['wins'] / lg['games'] * 100).round(1)
    profile['length'] = lg

    # ── Win rate by color ────────────────────────────────────────────────────
    cl = df.groupby('my_color').agg(
        games = ('outcome', 'count'),
        wins  = ('outcome', lambda x: (x == 'win').sum()),
    )
    cl['win_rate'] = (cl['wins'] / cl['games'] * 100).round(1)
    profile['color'] = cl

    # ── Error rates by outcome ───────────────────────────────────────────────
    profile['errors_by_outcome'] = df.groupby('outcome')[
        ['blunders', 'mistakes', 'inaccuracies']
    ].mean().round(3)

    # ── Monthly trend ────────────────────────────────────────────────────────
    df['month'] = df['date'].dt.to_period('M')
    mt = df.groupby('month').agg(
        games = ('outcome', 'count'),
        wins  = ('outcome', lambda x: (x == 'win').sum()),
    )
    mt['win_rate'] = (mt['wins'] / mt['games'] * 100).round(1)
    profile['monthly'] = mt

    # ── Weakness scores (0–100, higher = weaker) ────────────────────────────
    worst_opening_wr  = op['win_rate'].min()
    worst_length_wr   = lg['win_rate'].min()
    overall_wr        = (df['outcome'] == 'win').mean() * 100

    profile['weakness_scores'] = {
        'opening_gap'   : round(overall_wr - worst_opening_wr, 1),
        'length_gap'    : round(overall_wr - worst_length_wr, 1),
        'blunder_risk'  : round(df['blunders'].mean() * 100, 2),
        'positional_loss': round(
            (df[(df['outcome'] == 'loss') & (df['blunders'] == 0)].shape[0]
             / df[df['outcome'] == 'loss'].shape[0]) * 100, 1
        ),
    }

    return profile, df


# ── Run and print ────────────────────────────────────────────────────────────
profile, df = build_profile(df)

print("=" * 55)
print(f"  WEAKNESS PROFILE — {PLAYER}")
print("=" * 55)

print("\n── Opening win rates (worst first) ──")
print(profile['opening'][['games', 'wins', 'losses', 'win_rate']].to_string())

print("\n── Win rate by game length ──")
print(profile['length'][['games', 'wins', 'win_rate', 'blunders']].to_string())

print("\n── Win rate by color ──")
print(profile['color'][['games', 'wins', 'win_rate']].to_string())

print("\n── Error rates by outcome ──")
print(profile['errors_by_outcome'].to_string())

print("\n── Monthly trend ──")
print(profile['monthly'].to_string())

print("\n── Weakness scores (higher = bigger gap to fix) ──")
for k, v in profile['weakness_scores'].items():
    bar = "█" * int(v / 5)
    print(f"  {k:<20} {v:>6}   {bar}")

print("\n  positional_loss = % of losses with zero blunders")
print("  (how often you lose without making a single blunder)")