"""Where did each club's depth come from? Signings, departures, or players improving.
Premier League 2014/15-2025/26.

    py depth_sources.py

For every club that was in the league two seasons running, the change in depth (20th
percentile quality of regulars, 900+ min, rated on one scale across all seasons) is split
into four steps, done in this order:
  1. DEPARTURES   last season's squad minus regulars who left (or stopped being regulars)
  2. IMPROVEMENT  the regulars who stayed, rated on this season instead of last season
  3. PROMOTED     players already at the club who became regulars (academy, back from loan, rotation)
  4. SIGNINGS     regulars who weren't at the club last season
The four add up to the total change. Departures + signings = the transfer market.

DECISION RULE (set 29 Oct 2026, before running): Level 2 (transfer fees) is worth doing if the
transfer market (departures + signings) accounts for at least half of the combined depth gain
of Brighton, Aston Villa and Newcastle over 2019/20-2025/26.
"""
import re

import numpy as np
import pandas as pd

from config import RAW

U = RAW / "understat"
FIRST, LAST = 2014, 2025
RISERS = ["Brighton", "Aston Villa", "Newcastle United"]


def pos4(p):
    p = str(p).upper()
    if "GK" in p:
        return "GK"
    tokens = p.split()
    for code, label in (("D", "DEF"), ("M", "MID"), ("F", "ATT")):
        if code in tokens:
            return label
    return None


def zs(s):
    return (s - s.mean()) / s.std()


files = [f for f in U.glob("EPL_*.csv") if re.fullmatch(r"EPL_\d{4}\.csv", f.name) and FIRST <= int(f.stem[-4:]) <= LAST]
pl = pd.concat([pd.read_csv(f).assign(start=int(f.stem[-4:])) for f in files], ignore_index=True)
pl["team"] = pl.team_title.astype(str).str.split(",")
pl = pl.explode("team")
pl["team"] = pl.team.str.strip()
pl["id"] = (pl["id"].fillna(pl.player_name) if "id" in pl else pl.player_name).astype(str)
for c in ["time", "npxG", "xA", "xGChain", "xGBuildup"]:
    pl[c] = pd.to_numeric(pl[c], errors="coerce")
pl["pos4"] = pl.position.map(pos4)
pl = pl[pl.pos4.notna() & (pl.pos4 != "GK") & (pl.time > 0)].copy()

reg = pl[pl.time >= 900].copy()
for c in ["npxG", "xA", "xGChain", "xGBuildup"]:
    reg["z_" + c] = reg.assign(v=reg[c] / (reg.time / 90)).groupby("pos4").v.transform(zs)
reg["prod_p90"] = reg[["z_npxG", "z_xA", "z_xGChain", "z_xGBuildup"]].mean(axis=1)
reg["par"] = reg.prod_p90 - reg.groupby("pos4").prod_p90.transform(lambda s: s.quantile(0.20))
reg["q"] = 1 / (1 + np.exp(-reg.groupby("pos4").par.transform(zs)))
reg = reg.drop_duplicates(["id", "team", "start"])

q_of = reg.set_index(["id", "start"]).q.groupby(level=[0, 1]).first()
regulars = {k: set(g.id) for k, g in reg.groupby(["team", "start"])}
on_books = {k: set(g.id) for k, g in pl.groupby(["team", "start"])}   # any minutes for the club


def depth(ids, season):
    vals = [q_of.get((i, season), np.nan) for i in ids]
    vals = [v for v in vals if not np.isnan(v)]
    return np.quantile(vals, 0.20) if len(vals) >= 3 else np.nan


rows = []
for (team, s), now in regulars.items():
    last = regulars.get((team, s - 1))
    if last is None:
        continue
    stayers = now & last
    promoted = (now - last) & on_books.get((team, s - 1), set())
    signings = now - last - promoted
    d_last = depth(last, s - 1)
    d_stay_last = depth(stayers, s - 1)
    d_stay_now = depth(stayers, s)
    d_core = depth(stayers | promoted, s)
    d_now = depth(now, s)
    if np.isnan([d_last, d_stay_last, d_stay_now, d_core, d_now]).any():
        continue
    rows.append({"team": team, "start": s, "total": d_now - d_last,
                 "departures": d_stay_last - d_last, "improvement": d_stay_now - d_stay_last,
                 "promoted": d_core - d_stay_now, "signings": d_now - d_core,
                 "n_signed": len(signings), "n_left": len(last - now)})
df = pd.DataFrame(rows)
PARTS = ["departures", "improvement", "promoted", "signings"]
pd.set_option("display.width", 200)

recent = df[df.start >= 2019]
club = recent.groupby("team")[["total"] + PARTS + ["n_signed"]].sum()
club["seasons"] = recent.groupby("team").size()
club["market"] = club.departures + club.signings
club = club[club.seasons >= 4].sort_values("total", ascending=False)
print("1. CUMULATIVE DEPTH CHANGE BY SOURCE, 2019/20-2025/26 (clubs with 4+ consecutive-season pairs)")
print("   market = departures + signings. Positive = added depth.\n")
print(club[["seasons", "total", "market", "signings", "departures", "improvement", "promoted", "n_signed"]]
      .round(3).to_string())

r = club.loc[[t for t in RISERS if t in club.index]]
gain, market = r.total.sum(), r.market.sum()
share = market / gain if gain else np.nan
print(f"\n2. DECISION: Brighton + Villa + Newcastle gained {gain:+.3f} depth in total; "
      f"the transfer market accounts for {market:+.3f} ({share:.0%}).")
print(f"   -> Level 2 {'IS' if share >= 0.5 else 'is NOT'} worth doing (rule: transfer market >= 50% of their gain)")

print("\n3. WHOLE LEAGUE, ALL SEASONS: average contribution per club-season")
print(df[PARTS + ["total"]].mean().round(4).to_string())
print("\n4. SPURS AND MAN UNITED, 2019/20-2025/26, season by season")
for t in ["Tottenham", "Manchester United"]:
    print(f"\n   {t}")
    print(df[(df.team == t) & (df.start >= 2019)][["start", "total"] + PARTS + ["n_signed"]].round(3)
          .to_string(index=False).replace("\n", "\n   "))
print("\nNote: the order of steps affects how credit is split a little; totals are exact.")
