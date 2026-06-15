#!/usr/bin/env python3
"""
Parse squad data from Transfermarkt for all 18 Bundesliga clubs (25/26 season)
and update the SQLite database.
"""
import json
import sqlite3
import time
import sys
import os

# Transfermarkt club IDs for 2025/26 season
CLUBS = {
    "FC Bayern München":      {"tm_id": 27,  "tm_slug": "fc-bayern-munchen"},
    "Borussia Dortmund":      {"tm_id": 7,   "tm_slug": "borussia-dortmund"},
    "RB Leipzig":             {"tm_id": 1635, "tm_slug": "rb-leipzig"},
    "Bayer 04 Leverkusen":    {"tm_id": 6,   "tm_slug": "bayer-04-leverkusen"},
    "VfB Stuttgart":          {"tm_id": 16,  "tm_slug": "vfb-stuttgart"},
    "Eintracht Frankfurt":    {"tm_id": 91,  "tm_slug": "eintracht-frankfurt"},
    "Borussia Mönchengladbach":{"tm_id": 87,  "tm_slug": "borussia-moenchengladbach"},
    "SC Freiburg":            {"tm_id": 112, "tm_slug": "sc-freiburg"},
    "SV Werder Bremen":       {"tm_id": 134, "tm_slug": "sv-werder-bremen"},
    "TSG 1899 Hoffenheim":   {"tm_id": 175, "tm_slug": "tsg-1899-hoffenheim"},
    "1. FC Union Berlin":    {"tm_id": 80,  "tm_slug": "1-fc-union-berlin"},
    "Hamburger SV":           {"tm_id": 100, "tm_slug": "hamburger-sv"},
    "1. FC Köln":            {"tm_id": 65,  "tm_slug": "1-fc-koeln"},
    "1. FSV Mainz 05":       {"tm_id": 81,  "tm_slug": "1-fsv-mainz-05"},
    "FC Augsburg":            {"tm_id": 95,  "tm_slug": "fc-augsburg"},
    "SC Paderborn 07":        {"tm_id": 253, "tm_slug": "sc-paderborn-07"},
    "FC Schalke 04":          {"tm_id": 327, "tm_slug": "fc-schalke-04"},
    "SV Elversberg":          {"tm_id": 841, "tm_slug": "sv-elversberg"},
}

# Position mapping from Transfermarkt to our categories
POS_MAP = {
    "Goalkeeper": "GK",
    "Centre-Back": "DF",
    "Left-Back": "DF",
    "Right-Back": "DF",
    "Defensive Midfield": "MF",
    "Central Midfield": "MF",
    "Attacking Midfield": "MF",
    "Left Winger": "FW",
    "Right Winger": "FW",
    "Second Striker": "FW",
    "Centre-Forward": "FW",
}

# Nationality mapping (country code)
NAT_MAP = {
    "Germany": "GER", "France": "FRA", "England": "ENG", "Spain": "ESP",
    "Brazil": "BRA", "Argentina": "ARG", "Netherlands": "NED", "Portugal": "POR",
    "Austria": "AUT", "Switzerland": "SUI", "Croatia": "CRO", "Poland": "POL",
    "Denmark": "DEN", "Norway": "NOR", "Sweden": "SWE", "Italy": "ITA",
    "Belgium": "BEL", "Serbia": "SRB", "Czech Republic": "CZE", "Ukraine": "UKR",
    "Nigeria": "NGA", "Ghana": "GHA", "Cameroon": "CMR", "Ivory Coast": "CIV",
    "Japan": "JPN", "South Korea": "KOR", "Canada": "CAN", "USA": "USA",
    "Colombia": "COL", "Chile": "CHI", "Mexico": "MEX", "Turkey": "TUR",
    "Senegal": "SEN", "Mali": "MLI", "Algeria": "ALG", "Morocco": "MAR",
    "Egypt": "EGY", "Greece": "GRE", "Slovakia": "SVK", "Slovenia": "SVN",
    "Hungary": "HUN", "Romania": "ROU", "Bulgaria": "BGR", "Finland": "FIN",
    "Ireland": "IRL", "Northern Ireland": "NIR", "Scotland": "SCO", "Wales": "WAL",
    "Albania": "ALB", "Bosnia and Herzegovina": "BIH", "Montenegro": "MNE",
    "North Macedonia": "MKD", "Iceland": "ISL", "Estonia": "EST", "Latvia": "LVA",
    "Lithuania": "LTU", "Georgia": "GEO", "Armenia": "ARM", "Azerbaijan": "AZE",
    "Kazakhstan": "KAZ", "Uzbekistan": "UZB", "Iran": "IRN", "Australia": "AUS",
    "DR Congo": "COD", "Guinea": "GIN", "Burkina Faso": "BFA", "Togo": "TOG",
    "Angola": "AGO", "South Africa": "RSA", "Tunisia": "TUN", "Sierra Leone": "SLE",
    "Cape Verde": "CPV", "Mozambique": "MOZ", "Guatemala": "GUA", "Costa Rica": "CRC",
    "Honduras": "HON", "Panama": "PAN", "Jamaica": "JAM", "Haiti": "HAI",
    "Dominican Republic": "DOM", "Ecuador": "ECU", "Paraguay": "PRY", "Uruguay": "URU",
    "Venezuela": "VEN", "Peru": "PER", "Bolivia": "BOL", "Iraq": "IRQ",
    "Saudi Arabia": "KSA", "United Arab Emirates": "UAE", "Qatar": "QAT",
    "China": "CHN", "India": "IND", "Thailand": "THA", "Vietnam": "VNM",
    "Indonesia": "IDN", "Malaysia": "MAS", "Philippines": "PHI", "New Zealand": "NZL",
    "Israel": "ISR", "Cyprus": "CYP", "Luxembourg": "LUX", "Malta": "MLT",
    "Liechtenstein": "LIE", "San Marino": "SMR", "Andorra": "AND",
    "Kosovo": "KOS", "Moldova": "MDA", "Belarus": "BLR", "Russia": "RUS",
}

# Clubs considered "German" for foreigner detection
GERMAN_CLUBS = set(CLUBS.keys())


def map_position(tm_pos: str) -> str:
    """Map Transfermarkt position to GK/DF/MF/FW."""
    tm_pos = tm_pos.strip()
    if tm_pos in POS_MAP:
        return POS_MAP[tm_pos]
    # Fallback: check keywords
    if "Goalkeeper" in tm_pos or "Keeper" in tm_pos:
        return "GK"
    if "Back" in tm_pos or "Wing-Back" in tm_pos or "Centre-Back" in tm_pos:
        return "DF"
    if "Midfield" in tm_pos or "Midfielder" in tm_pos:
        return "MF"
    if "Forward" in tm_pos or "Striker" in tm_pos or "Winger" in tm_pos:
        return "FW"
    return "MF"  # default


def map_nationality(tm_nat: str) -> str:
    """Map Transfermarkt nationality to country code."""
    tm_nat = tm_nat.strip()
    if tm_nat in NAT_MAP:
        return NAT_MAP[tm_nat]
    # Try partial match
    for full, code in NAT_MAP.items():
        if full in tm_nat or tm_nat in full:
            return code
    return tm_nat[:3].upper() if tm_nat else "???"


def is_foreigner(nationality: str) -> bool:
    """Check if player is foreigner (non-German)."""
    return nationality != "GER"


def clean_name(name: str) -> str:
    """Clean player name from extra whitespace and newlines."""
    # Take only first line (name, not position that TM sometimes appends)
    lines = name.strip().split('\n')
    return lines[0].strip()


def get_players_from_html(html_source: str) -> list:
    """Parse players from Transfermarkt HTML source."""
    from html.parser import HTMLParser
    
    players = []
    # Simple regex-based parsing
    import re
    
    # Find player rows in the table
    # Pattern: <td class="zentriert">number</td> ... <td class=""><a ...>name</a></td> ... <td class="">position</td>
    row_pattern = re.compile(
        r'<tr[^>]*class=\"(odd|even)\"[^>]*>(.*?)</tr>',
        re.DOTALL
    )
    
    for match in row_pattern.finditer(html_source):
        row_html = match.group(2)
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row_html, re.DOTALL)
        
        if len(cells) < 5:
            continue
        
        # Extract number
        number = re.sub(r'<[^>]+>', '', cells[0]).strip()
        
        # Extract name (from link)
        name_match = re.search(r'<a[^>]*>(.*?)</a>', cells[1], re.DOTALL)
        if not name_match:
            continue
        name = re.sub(r'<[^>]+>', '', name_match.group(1)).strip()
        
        # Extract position
        pos = re.sub(r'<[^>]+>', '', cells[2]).strip()
        
        # Extract nationality (from flag title or text)
        nat_match = re.search(r'title=\"([^\"]+)\"', cells[4])
        if nat_match:
            nat = nat_match.group(1)
        else:
            nat = re.sub(r'<[^>]+>', '', cells[4]).strip()
        
        if name and pos:
            players.append({
                'name': name,
                'position': pos,
                'number': number if number else None,
                'nationality': nat,
            })
    
    return players


def update_club_squad(db_path: str, club_name: str, players: list):
    """Update squad data in database for a club."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Delete old players for this club
    c.execute("DELETE FROM players WHERE club_name = ?", (club_name,))
    
    # Insert new players
    for p in players:
        pos = map_position(p['position'])
        nat = map_nationality(p['nationality'])
        foreign = 1 if is_foreigner(nat) else 0
        name = clean_name(p['name'])
        number = p['number']
        
        c.execute("""
            INSERT INTO players (club_name, name, number, position, nationality, is_foreigner)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (club_name, name, number, pos, nat, foreign))
    
    conn.commit()
    count = c.execute("SELECT COUNT(*) FROM players WHERE club_name = ?", (club_name,)).fetchone()[0]
    conn.close()
    return count


if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), "bundesliga_today.db")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        print("Clubs to parse:")
        for name, info in CLUBS.items():
            print(f"  {info['tm_id']:4d} | {info['tm_slug']:40s} | {name}")
        sys.exit(0)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--club":
        # Parse single club: --club "FC Bayern München" < html_file
        club_name = sys.argv[2]
        html = sys.stdin.read()
        players = get_players_from_html(html)
        count = update_club_squad(db_path, club_name, players)
        print(f"Updated {club_name}: {count} players")
        sys.exit(0)
    
    print("Usage:")
    print("  --list                    List all clubs")
    print('  --club "Name" < file.html  Parse HTML file for a club')
