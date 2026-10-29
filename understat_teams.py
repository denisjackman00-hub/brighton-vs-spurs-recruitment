"""Download Premier League team match data from Understat (one request per season).

    py -m loaders.understat_teams --from 2014 --to 2026

Saves data/raw/understat/EPL_teams_<season>.csv, one row per team per match:
date, home/away, npxG (for), npxGA (against), goals for/against, points,
and PPDA (passes allowed per defensive action: lower = more intense pressing).
Seasons already saved are skipped, except the current one, which is refreshed.
"""
import argparse
import time
from datetime import date

import pandas as pd

from config import RAW

OUT = RAW / "understat"


def fetch(year_from, year_to, league="EPL", delay=3):
    from understatapi import UnderstatClient

    OUT.mkdir(parents=True, exist_ok=True)
    current = date.today().year if date.today().month >= 7 else date.today().year - 1
    with UnderstatClient() as client:
        for season in range(year_from, year_to + 1):
            path = OUT / f"{league}_teams_{season}.csv"
            if path.exists() and season != current:
                print(f"  [skip] {path.name} already saved")
                continue
            try:
                teams = client.league(league=league).get_team_data(season=str(season))
            except Exception as e:
                print(f"  [error] {league} {season}: {e}")
                continue
            rows = []
            for t in teams.values():
                for g in t.get("history", []):
                    ppda, ppda_allowed = g.get("ppda") or {}, g.get("ppda_allowed") or {}
                    rows.append({
                        "season": f"{season}-{season + 1}", "team": t.get("title"),
                        "date": str(g.get("date", ""))[:10], "venue": g.get("h_a"),
                        "npxG": float(g.get("npxG", 0)), "npxGA": float(g.get("npxGA", 0)),
                        "xG": float(g.get("xG", 0)), "xGA": float(g.get("xGA", 0)),
                        "goals_for": int(g.get("scored", 0)), "goals_against": int(g.get("missed", 0)),
                        "pts": int(g.get("pts", 0)),
                        "ppda_passes": float(ppda.get("att", 0)), "ppda_actions": float(ppda.get("def", 0)),
                        "opp_ppda_passes": float(ppda_allowed.get("att", 0)),
                        "opp_ppda_actions": float(ppda_allowed.get("def", 0)),
                    })
            df = pd.DataFrame(rows).sort_values(["team", "date"])
            df.to_csv(path, index=False)
            print(f"  [ok] {league} {season}-{season + 1}: {df.team.nunique()} teams, {len(df)} team-matches")
            time.sleep(delay)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--from", dest="y0", type=int, default=2014)
    p.add_argument("--to", dest="y1", type=int, default=2026)
    a = p.parse_args()
    fetch(a.y0, a.y1)
