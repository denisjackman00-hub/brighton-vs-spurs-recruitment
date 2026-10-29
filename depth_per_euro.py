"""Level 2: how much squad depth did each Premier League club get for its money? 2019/20-2025/26.

    py depth_per_euro.py

Depth changes come from depth_sources.py (run silently here). Money comes from Transfermarkt
(player-scores dataset on Kaggle, CC0): fees paid for players coming in, fees received for
players going out, per club, transfer seasons 19/20 to 25/26 (summer + January).

Caveats printed with the results:
  - fees marked unknown (undisclosed) count as zero; the share of unknown fees is shown per club
  - loans and free transfers have no fee
  - wages are not included, and for many clubs wages matter more than fees
"""
import contextlib
import io

import pandas as pd

from config import RAW

with contextlib.redirect_stdout(io.StringIO()):
    import depth_sources as ds          # builds ds.df: one row per club-season with the depth breakdown

FIRST, LAST = 2019, 2025
# Understat name -> Transfermarkt short name
TM_NAME = {"Manchester United": "Man Utd", "Manchester City": "Man City", "Newcastle United": "Newcastle",
           "Wolverhampton Wanderers": "Wolves", "Tottenham": "Tottenham", "West Ham": "West Ham",
           "Brighton": "Brighton", "Nottingham Forest": "Nottm Forest", "Leicester": "Leicester",
           "Sheffield United": "Sheff Utd", "Leeds": "Leeds", "Luton": "Luton"}

tr = pd.read_csv(RAW / "transfermarkt" / "transfers.csv")
tr["start"] = 2000 + pd.to_numeric(tr.transfer_season.str[:2], errors="coerce")
tr = tr[tr.start.between(FIRST, LAST)]
all_tr = pd.read_csv(RAW / "transfermarkt" / "transfers.csv", usecols=["to_club_id", "to_club_name"])

dep = ds.df[ds.df.start.between(FIRST, LAST)]
club = dep.groupby("team")[["total", "signings", "departures", "improvement", "promoted"]].sum()
club["seasons"] = dep.groupby("team").size()
club = club[club.seasons >= 4]

rows, missing = [], []
for team in club.index:
    tm = TM_NAME.get(team, team)
    ids = all_tr[all_tr.to_club_name == tm].to_club_id
    if ids.empty:
        missing.append(team)
        continue
    cid = ids.mode().iloc[0]            # the club's Transfermarkt id (avoids same-name clubs elsewhere)
    ins, outs = tr[tr.to_club_id == cid], tr[tr.from_club_id == cid]
    rows.append({"team": team, "spent_m": ins.transfer_fee.fillna(0).sum() / 1e6,
                 "received_m": outs.transfer_fee.fillna(0).sum() / 1e6,
                 "n_in": len(ins), "fee_unknown": ins.transfer_fee.isna().mean()})
money = pd.DataFrame(rows).set_index("team")
out = club.join(money, how="inner")
out["net_m"] = out.spent_m - out.received_m
out["market"] = out.signings + out.departures
out["depth_per_100m_spent"] = out.total / out.spent_m * 100

pd.set_option("display.width", 220)
print(f"Premier League clubs with 4+ consecutive seasons, transfer seasons {FIRST % 100}/{FIRST % 100 + 1} "
      f"to {LAST % 100}/{LAST % 100 + 1}. Money in EUR millions.\n")
cols = ["seasons", "spent_m", "received_m", "net_m", "fee_unknown", "total", "market", "depth_per_100m_spent"]
print(out.sort_values("depth_per_100m_spent", ascending=False)[cols].round(
    {"spent_m": 0, "received_m": 0, "net_m": 0, "fee_unknown": 2, "total": 3, "market": 3,
     "depth_per_100m_spent": 3}).to_string())
if missing:
    print(f"\nNo Transfermarkt match for: {missing}  (add them to TM_NAME at the top)")

r = out[["spent_m", "net_m", "total"]].corr().round(2)
print(f"\nAcross clubs: correlation of depth gained with gross spend {r.loc['spent_m', 'total']:+.2f}, "
      f"with net spend {r.loc['net_m', 'total']:+.2f}")
print("(near zero = money alone doesn't explain who built depth; strongly positive = it mostly does)")
print("\nCaveats: undisclosed fees count as 0, loans and frees have no fee, wages not included.")
