"""Ceiling test: does spending buy depth once we allow for where each club started?
Premier League, club-seasons 2019/20-2025/26.

    py ceiling_test.py

Problem with the simple comparison: clubs that already had deep squads (City) have little room
to add depth, and clubs starting low (Brighton, Palace) have lots. So we compare club-seasons
with the same starting depth and ask whether the ones that spent more gained more.

Model (one row per club per season, clustered by club):
    change in depth = a + b x last season's depth + c x spending that transfer window (EUR 100m)
Run with gross spend and with net spend.

PRE-REGISTERED (29 Oct 2026, before running):
  MAIN: with starting depth in the model, gross spend has a positive effect, z >= 1.65.
  PASS = money does buy depth once the ceiling is allowed for.
  FAIL = even comparing like with like, spending doesn't predict depth gained.
"""
import contextlib
import io

import numpy as np
import pandas as pd

from config import RAW

with contextlib.redirect_stdout(io.StringIO()):
    import depth_sources as ds

FIRST, LAST = 2019, 2025
TM_NAME = {"Manchester United": "Man Utd", "Manchester City": "Man City", "Newcastle United": "Newcastle",
           "Wolverhampton Wanderers": "Wolves", "Tottenham": "Tottenham", "West Ham": "West Ham",
           "Brighton": "Brighton", "Nottingham Forest": "Nottm Forest", "Leicester": "Leicester",
           "Sheffield United": "Sheff Utd", "Leeds": "Leeds", "Luton": "Luton"}

tr = pd.read_csv(RAW / "transfermarkt" / "transfers.csv")
tr["start"] = 2000 + pd.to_numeric(tr.transfer_season.str[:2], errors="coerce")
tr["fee"] = tr.transfer_fee.fillna(0)

df = ds.df[ds.df.start.between(FIRST, LAST)].copy()
df["start_depth"] = [ds.depth(ds.regulars[(t, s - 1)], s - 1) for t, s in zip(df.team, df.start)]

ids, missing = {}, []
for team in df.team.unique():
    m = tr[tr.to_club_name == TM_NAME.get(team, team)].to_club_id
    if m.empty:
        missing.append(team)
    else:
        ids[team] = m.mode().iloc[0]
spent = tr.groupby(["to_club_id", "start"]).fee.sum() / 1e8          # EUR 100m
received = tr.groupby(["from_club_id", "start"]).fee.sum() / 1e8
df = df[df.team.isin(ids)].copy()
df["gross"] = [spent.get((ids[t], s), 0.0) for t, s in zip(df.team, df.start)]
df["net"] = df.gross - [received.get((ids[t], s), 0.0) for t, s in zip(df.team, df.start)]
df["market"] = df.signings + df.departures


def ols(d, y, xs, cluster="team"):
    d = d.dropna(subset=[y] + xs).reset_index(drop=True)
    X = np.column_stack([np.ones(len(d))] + [d[x].values.astype(float) for x in xs])
    Y = d[y].values
    XtX_inv = np.linalg.pinv(X.T @ X)
    b = XtX_inv @ X.T @ Y
    e = Y - X @ b
    meat = np.zeros((X.shape[1], X.shape[1]))
    for _, idx in d.groupby(cluster).indices.items():
        s = X[idx].T @ e[idx]
        meat += np.outer(s, s)
    G, n, k = d[cluster].nunique(), len(d), X.shape[1]
    V = XtX_inv @ meat @ XtX_inv * (G / (G - 1)) * ((n - 1) / (n - k))
    se = np.sqrt(np.diag(V))
    r2 = 1 - (e ** 2).sum() / ((Y - Y.mean()) ** 2).sum()
    return pd.DataFrame({"coef": b, "se": se, "z": b / se}, index=["const"] + xs), r2, n


NAMES = {"start_depth": "starting depth", "gross": "gross spend (per EUR 100m)", "net": "net spend (per EUR 100m)"}
print(f"{len(df)} club-seasons, {df.team.nunique()} clubs, {FIRST % 100}/{FIRST % 100 + 1} to {LAST % 100}/{LAST % 100 + 1}.")
if missing:
    print(f"No Transfermarkt match (left out): {missing}")
print(f"Average spend per club-season: gross EUR {df.gross.mean() * 100:.0f}m, net EUR {df.net.mean() * 100:.0f}m.\n")

for y, ylabel in [("total", "TOTAL depth change"), ("market", "depth change from the transfer market")]:
    print(f"Outcome: {ylabel}")
    for xs in [["gross"], ["start_depth"], ["start_depth", "gross"], ["start_depth", "net"]]:
        r, r2, n = ols(df, y, xs)
        parts = "   ".join(f"{NAMES[x]} {r.loc[x, 'coef']:+.4f} (z {r.loc[x, 'z']:+.2f})" for x in xs)
        print(f"  R² {r2:.3f}  n {n}   {parts}")
    print()

r, _, _ = ols(df, "total", ["start_depth", "gross"])
b, z, se = r.loc["gross", "coef"], r.loc["gross", "z"], r.loc["gross", "se"]
print(f"MAIN TEST: allowing for starting depth, each EUR 100m of gross spend adds {b:+.4f} depth "
      f"(95% range {b - 1.96 * se:+.4f} to {b + 1.96 * se:+.4f}), z = {z:.2f} -> "
      f"{'PASS' if (b > 0 and z >= 1.65) else 'FAIL'} (bar: positive, z >= 1.65)")
sd = df.groupby("start").total.std().mean()
print(f"For scale: a typical club's depth changes by about {sd:.3f} (1 SD) in a season.")
c = r.loc["start_depth", "coef"]
print(f"Ceiling check: starting depth coefficient {c:+.3f} "
      f"({'deeper squads do tend to fall back' if c < 0 else 'no sign of a ceiling'}).")

print("\nWho beat or missed what the model expected, given starting depth and spend (summed over seasons):")
X = np.column_stack([np.ones(len(df)), df.start_depth, df.gross])
df["vs_expected"] = df.total - X @ r.coef.values
tab = df.groupby("team").agg(seasons=("start", "size"), gross_m=("gross", lambda s: s.sum() * 100),
                             depth_change=("total", "sum"), vs_expected=("vs_expected", "sum"))
print(tab.sort_values("vs_expected", ascending=False).round({"gross_m": 0, "depth_change": 3, "vs_expected": 3}).to_string())
