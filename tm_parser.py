#!/usr/bin/env python3
"""
Master script to parse all 18 Bundesliga clubs from Transfermarkt.
Uses browser JS injection to extract player data.
"""
import json
import sqlite3
import os
import sys
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "bundesliga_today.db")

# Transfermarkt data: slug -> (verein_id, db_club_name)
# Found via search on transfermarkt.com
CLUBS_TM = [
    # (tm_slug, verein_id, db_club_name) — db_club_name is the LIKE pattern
    ("fc-bayern-munchen", 27, "Bayern München"),
    ("borussia-dortmund", 16, "Dortmund"),
    ("rasenballsport-leipzig", 23826, "Leipzig"),
    ("bayer-04-leverkusen", 6, "Leverkusen"),  # need to verify
    ("vfb-stuttgart", 16, "Stuttgart"),  # need to verify
    ("eintracht-frankfurt", 91, "Frankfurt"),  # need to verify
    ("borussia-moenchengladbach", 87, "Mönchengladbach"),  # need to verify
    ("sc-freiburg", 112, "Freiburg"),  # need to verify
    ("sv-werder-bremen", 134, "Bremen"),  # need to verify
    ("tsg-1899-hoffenheim", 175, "Hoffenheim"),  # need to verify
    ("1-fc-union-berlin", 80, "Union Berlin"),  # need to verify
    ("hamburger-sv", 100, "Hamburger"),  # need to verify
    ("1-fc-koeln", 65, "Köln"),  # need to verify
    ("1-fsv-mainz-05", 81, "Mainz"),  # need to verify
    ("fc-augsburg", 95, "Augsburg"),  # need to verify
    ("sc-paderborn-07", 253, "Paderborn"),  # need to verify
    ("fc-schalke-04", 327, "Schalke"),  # need to verify
    ("sv-elversberg", 841, "Elversberg"),  # need to verify
]

# JS parser to inject
JS_PARSER = """
(function() {
  var posClassMap = {'bg_Torwart':'GK','bg_Abwehr':'DF','bg_Mittelfeld':'MF','bg_Sturm':'FW'};
  var rows = document.querySelectorAll('table.items tbody tr');
  var players = [];
  rows.forEach(function(row) {
    var cells = row.querySelectorAll('td');
    if (cells.length < 7) return;
    var numCell = cells[0];
    var numDiv = numCell ? numCell.querySelector('.rn_nummer') : null;
    var number = numDiv ? numDiv.innerText.trim() : '';
    var posClass = numCell ? numCell.className : '';
    var position = 'MF';
    for (var cls in posClassMap) {
      if (posClass.indexOf(cls) !== -1) { position = posClassMap[cls]; break; }
    }
    var name = '';
    var nameLink = cells[1] ? cells[1].querySelector('.hauptlink a') : null;
    if (!nameLink) nameLink = cells[3] ? cells[3].querySelector('a') : null;
    if (nameLink) name = nameLink.innerText.trim();
    var flagImg = cells[6] ? cells[6].querySelector('img.flaggenrahmen, img[class*="flagge"]') : null;
    if (!flagImg) flagImg = cells[6] ? cells[6].querySelector('img') : null;
    var nat = flagImg ? (flagImg.getAttribute('title') || flagImg.getAttribute('alt') || '') : '';
    if (name && nat) players.push({name:name, number:number, position:position, nationality:nat});
  });
  return JSON.stringify({count:players.length, players:players});
})()
"""

if __name__ == "__main__":
    print("This script provides the JS parser and club list for browser-based parsing.")
    print("Use with browser_console tool to extract data.")
    print()
    print("JS Parser:")
    print(JS_PARSER)
    print()
    print("Clubs:")
    for slug, vid, name in CLUBS_TM:
        print(f"  {slug:40s} verein/{vid:6d}  {name}")
