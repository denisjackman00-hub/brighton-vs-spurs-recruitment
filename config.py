"""Paths and competition definitions. Edit here, not in the loaders."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "football.sqlite"
RAW = ROOT / "data" / "raw"
RAW_FOOTBALL_DATA = RAW / "football_data"   # football-data.co.uk CSVs you downloaded
RAW_UEFA_PAGES = RAW / "uefa_pages"         # worldfootball pages saved from your browser
RAW_CLUBELO = RAW / "clubelo"               # cached Club Elo CSVs
REFERENCE = ROOT / "reference"              # hand-maintained CSVs (aliases, calendars, pitches)

# comp_code: (name, comp_type, country, tier, calendar)
COMPETITIONS = {
    # football-data.co.uk main leagues (one CSV per season)
    "E0": ("Premier League", "league", "ENG", 1, "winter"),
    "E1": ("Championship", "league", "ENG", 2, "winter"),
    "E2": ("League One", "league", "ENG", 3, "winter"),
    "E3": ("League Two", "league", "ENG", 4, "winter"),
    "EC": ("National League", "league", "ENG", 5, "winter"),
    "SC0": ("Scottish Premiership", "league", "SCO", 1, "winter"),
    "SC1": ("Scottish Championship", "league", "SCO", 2, "winter"),
    "SC2": ("Scottish League One", "league", "SCO", 3, "winter"),
    "SC3": ("Scottish League Two", "league", "SCO", 4, "winter"),
    "D1": ("Bundesliga", "league", "GER", 1, "winter"),
    "D2": ("2. Bundesliga", "league", "GER", 2, "winter"),
    "I1": ("Serie A", "league", "ITA", 1, "winter"),
    "I2": ("Serie B", "league", "ITA", 2, "winter"),
    "SP1": ("La Liga", "league", "ESP", 1, "winter"),
    "SP2": ("Segunda Division", "league", "ESP", 2, "winter"),
    "F1": ("Ligue 1", "league", "FRA", 1, "winter"),
    "F2": ("Ligue 2", "league", "FRA", 2, "winter"),
    "N1": ("Eredivisie", "league", "NED", 1, "winter"),
    "B1": ("Belgian Pro League", "league", "BEL", 1, "winter"),
    "P1": ("Primeira Liga", "league", "POR", 1, "winter"),
    "T1": ("Super Lig", "league", "TUR", 1, "winter"),
    "G1": ("Greek Super League", "league", "GRE", 1, "winter"),
    # football-data.co.uk "extra" leagues (one CSV per country, all seasons) - European ones
    "AUT": ("Austrian Bundesliga", "league", "AUT", 1, "winter"),
    "DNK": ("Danish Superliga", "league", "DEN", 1, "winter"),
    "FIN": ("Veikkausliiga", "league", "FIN", 1, "summer"),
    "IRL": ("League of Ireland Premier Division", "league", "IRL", 1, "summer"),
    "NOR": ("Eliteserien", "league", "NOR", 1, "summer"),
    "POL": ("Ekstraklasa", "league", "POL", 1, "winter"),
    "ROU": ("Liga I", "league", "ROU", 1, "winter"),
    "RUS": ("Russian Premier League", "league", "RUS", 1, "winter"),
    "SWE": ("Allsvenskan", "league", "SWE", 1, "summer"),
    "SWZ": ("Swiss Super League", "league", "SUI", 1, "winter"),
    # UEFA competitions (from saved worldfootball pages)
    "CL": ("Champions League", "uefa", None, None, None),
    "CL_Q": ("Champions League qualifying", "uefa", None, None, None),
    "EL": ("Europa League", "uefa", None, None, None),
    "EL_Q": ("Europa League qualifying", "uefa", None, None, None),
    "ECL": ("Conference League", "uefa", None, None, None),
    "ECL_Q": ("Conference League qualifying", "uefa", None, None, None),
}

# Countries whose top league plays a spring-to-autumn (summer) calendar.
# Approximate: Georgia was autumn-spring in 2013-2016; Moldova and Armenia have
# switched back and forth, so they are left out.
SUMMER_COUNTRIES = {"NOR", "SWE", "FIN", "IRL", "ISL", "FRO", "EST", "LVA", "LTU", "BLR", "KAZ", "GEO"}

EXTRA_LEAGUE_CODES ={"AUT", "DNK", "FIN", "IRL", "NOR", "POL", "ROU", "RUS", "SWE", "SWZ"}
