#!/usr/bin/env python3
"""
Update squad data in DB from parsed Transfermarkt data.
Usage: python3 update_squads.py
Reads JSON data from stdin or from file.
"""
import json
import sqlite3
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "bundesliga_today.db")

# Nationality name -> ISO 3-letter code
NAT_MAP = {
    "Germany": "GER", "France": "FRA", "England": "ENG", "Spain": "ESP",
    "Brazil": "BRA", "Argentina": "ARG", "Netherlands": "NED", "Portugal": "POR",
    "Austria": "AUT", "Switzerland": "SUI", "Croatia": "CRO", "Poland": "POL",
    "Denmark": "DEN", "Norway": "NOR", "Sweden": "SWE", "Italy": "ITA",
    "Belgium": "BEL", "Serbia": "SRB", "Czech Republic": "CZE", "Ukraine": "UKR",
    "Nigeria": "NGA", "Ghana": "GHA", "Cameroon": "CMR", "Ivory Coast": "CIV",
    "Japan": "JPN", "Korea, South": "KOR", "South Korea": "KOR", "Canada": "CAN",
    "United States": "USA", "USA": "USA", "Colombia": "COL", "Chile": "CHI",
    "Mexico": "MEX", "Türkiye": "TUR", "Turkey": "TUR", "Senegal": "SEN",
    "Mali": "MLI", "Algeria": "ALG", "Morocco": "MAR", "Egypt": "EGY",
    "Greece": "GRE", "Slovakia": "SVK", "Slovenia": "SVN", "Hungary": "HUN",
    "Romania": "ROU", "Bulgaria": "BGR", "Finland": "FIN", "Ireland": "IRL",
    "Northern Ireland": "NIR", "Scotland": "SCO", "Wales": "WAL", "Albania": "ALB",
    "Bosnia and Herzegovina": "BIH", "Montenegro": "MNE", "North Macedonia": "MKD",
    "Iceland": "ISL", "Estonia": "EST", "Latvia": "LVA", "Lithuania": "LTU",
    "Georgia": "GEO", "Armenia": "ARM", "Azerbaijan": "AZE", "Kazakhstan": "KAZ",
    "Uzbekistan": "UZB", "Iran": "IRN", "Australia": "AUS", "DR Congo": "COD",
    "Guinea": "GIN", "Burkina Faso": "BFA", "Togo": "TOG", "Angola": "AGO",
    "South Africa": "RSA", "Tunisia": "TUN", "Sierra Leone": "SLE",
    "Cape Verde": "CPV", "Mozambique": "MOZ", "Israel": "ISR", "Cyprus": "CYP",
    "Luxembourg": "LUX", "Kosovo": "KOS", "Moldova": "MDA", "Belarus": "BLR",
    "Russia": "RUS", "Equatorial Guinea": "EQG", "Guinea-Bissau": "GNB",
    "Madagascar": "MDG", "Comoros": "COM", "Gambia": "GAM", "Benin": "BEN",
    "Liberia": "LBR", "Zambia": "ZAM", "Zimbabwe": "ZIM", "Congo": "CGO",
    "Central African Republic": "CTA", "Sudan": "SDN", "Ethiopia": "ETH",
    "Kenya": "KEN", "Uganda": "UGA", "Tanzania": "TAN", "Namibia": "NAM",
    "Botswana": "BOT", "Mauritius": "MRI", "Seychelles": "SEY",
    "New Zealand": "NZL", "China": "CHN", "India": "IND", "Thailand": "THA",
    "Vietnam": "VNM", "Indonesia": "IDN", "Malaysia": "MAS", "Philippines": "PHI",
    "Iraq": "IRQ", "Saudi Arabia": "KSA", "United Arab Emirates": "UAE",
    "Qatar": "QAT", "Jordan": "JOR", "Lebanon": "LIB", "Syria": "SYR",
    "Kuwait": "KUW", "Bahrain": "BHN", "Oman": "OMA", "Yemen": "YEM",
    "Afghanistan": "AFG", "Pakistan": "PAK", "Bangladesh": "BAN",
    "Sri Lanka": "SRI", "Nepal": "NEP", "Myanmar": "MYA", "Cambodia": "CAM",
    "Laos": "LAO", "Mongolia": "MGL", "Taiwan": "TWN", "Hong Kong": "HKG",
    "Macau": "MAC", "Singapore": "SIN", "Brunei": "BRU", "Maldives": "MDV",
    "Bhutan": "BHU", "Timor-Leste": "TLS", "Papua New Guinea": "PNG",
    "Fiji": "FIJ", "Samoa": "SAM", "Tonga": "TGA", "Vanuatu": "VUT",
    "Solomon Islands": "SOL", "Kiribati": "KIR", "Tuvalu": "TUV",
    "Marshall Islands": "MHL", "Palau": "PLW", "Micronesia": "FSM",
}


def map_nationality(name):
    name = name.strip()
    if name in NAT_MAP:
        return NAT_MAP[name]
    # Fallback: first 3 letters uppercase
    return name[:3].upper() if len(name) >= 3 else name.upper()


def get_club_db_name(conn, tm_name):
    """Find club name in DB matching Transfermarkt name."""
    c = conn.cursor()
    # Try exact match first
    row = c.execute("SELECT name FROM clubs WHERE name LIKE ?", (f"%{tm_name}%",)).fetchone()
    if row:
        return row[0]
    # Try short_name match
    row = c.execute("SELECT name FROM clubs WHERE short_name LIKE ?", (f"%{tm_name[:3]}%",)).fetchone()
    if row:
        return row[0]
    return None


def update_squad(conn, club_db_name, players):
    c = conn.cursor()
    # Delete old players
    c.execute("DELETE FROM players WHERE club_name = ?", (club_db_name,))
    
    for p in players:
        nat = map_nationality(p['nationality'])
        is_foreign = 0 if nat == "GER" else 1
        number = p['number']
        try:
            number = int(number) if number else None
        except ValueError:
            number = None
        
        c.execute("""
            INSERT INTO players (club_name, name, number, position, nationality, is_foreigner)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (club_db_name, p['name'], number, p['position'], nat, is_foreign))
    
    conn.commit()
    count = c.execute("SELECT COUNT(*) FROM players WHERE club_name = ?", (club_db_name,)).fetchone()[0]
    return count


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 update_squads.py <club_db_name> <json_file>")
        print("   or: echo '{...}' | python3 update_squads.py <club_db_name> -")
        sys.exit(1)
    
    club_name = sys.argv[1]
    json_source = sys.argv[2]
    
    if json_source == "-":
        data = json.load(sys.stdin)
    else:
        with open(json_source, 'r') as f:
            data = json.load(f)
    
    players = data if isinstance(data, list) else data.get('players', [])
    
    conn = sqlite3.connect(DB_PATH)
    count = update_squad(conn, club_name, players)
    foreigners = conn.execute("SELECT COUNT(*) FROM players WHERE club_name = ? AND is_foreigner = 1", (club_name,)).fetchone()[0]
    
    print(f"Updated {club_name}: {count} players, {foreigners} foreigners")
    
    # Show by position
    for pos in ['GK', 'DF', 'MF', 'FW']:
        rows = conn.execute("SELECT name, number, nationality FROM players WHERE club_name = ? AND position = ? ORDER BY number", (club_name, pos)).fetchall()
        if rows:
            print(f"  [{pos}] ({len(rows)})")
            for r in rows:
                print(f"    #{r[1] or '—'} {r[0]} ({r[2]})")
    
    conn.close()
