"""Download Premier League player-season stats from Understat (one request per season).

    py -m pip install understatapi
    py -m loaders.understat --from 2014 --to 2025

Season 2019 means 2019/20. Saves data/raw/understat/EPL_<season>.csv; seasons already
saved are skipped, so it's safe to re-run. Columns include player_name, team_title,
position, time (minutes), npxG, xA, xGChain, xGBuildup.
"""
import argparse
import time

import pandas as pd

from config import RAW

OUT = RAW / "understat"


def fetch(year_from, year_to, league="EPL", delay=3):
    from understatapi import UnderstatClient

    OUT.mkdir(parents=True, exist_ok=True)
    with UnderstatClient() as client:
        for season in range(year_from, year_to + 1):
            path = OUT / f"{league}_{season}.csv"
            if path.exists():
                print(f"  [skip] {path.name} already saved")
                continue
            try:
                rows = client.league(league=league).get_player_data(season=str(season))
            except Exception as e:  # network errors, site changes
                print(f"  [error] {league} {season}: {e}")
                continue
            df = pd.DataFrame(rows)
            df.insert(0, "season", f"{season}-{season + 1}")
            df.to_csv(path, index=False)
            print(f"  [ok] {league} {season}-{season + 1}: {len(df)} players")
            time.sleep(delay)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--from", dest="y0", type=int, default=2014)
    p.add_argument("--to", dest="y1", type=int, default=2025)
    a = p.parse_args()
    fetch(a.y0, a.y1)
