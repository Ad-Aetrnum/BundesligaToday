#!/usr/bin/env python3
"""
Save all collected Transfermarkt player data to JSON files.
Each club is saved as a separate JSON file.
"""
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "tm_data")
os.makedirs(DATA_DIR, exist_ok=True)

CLUBS_DATA = {
    "Bayer 04 Leverkusen": [
        {"name": "Mark Flekken", "number": "1", "position": "GK", "nationality": "Netherlands"},
        {"name": "Jonas Omlin", "number": "18", "position": "GK", "nationality": "Switzerland"},
        {"name": "Janis Blaswich", "number": "28", "position": "GK", "nationality": "Germany"},
        {"name": "Niklas Lomb", "number": "36", "position": "GK", "nationality": "Germany"},
        {"name": "Jarell Quansah", "number": "4", "position": "DF", "nationality": "England"},
        {"name": "Edmond Tapsoba", "number": "12", "position": "DF", "nationality": "Burkina Faso"},
        {"name": "Loïc Badé", "number": "5", "position": "DF", "nationality": "France"},
        {"name": "Axel Tape", "number": "16", "position": "DF", "nationality": "France"},
        {"name": "Tim Oermann", "number": "15", "position": "DF", "nationality": "Germany"},
        {"name": "Issa Traoré", "number": "41", "position": "DF", "nationality": "Mali"},
        {"name": "Alejandro Grimaldo", "number": "20", "position": "DF", "nationality": "Spain"},
        {"name": "Arthur", "number": "13", "position": "DF", "nationality": "Brazil"},
        {"name": "Lucas Vázquez", "number": "21", "position": "DF", "nationality": "Spain"},
        {"name": "Equi Fernández", "number": "6", "position": "MF", "nationality": "Argentina"},
        {"name": "Robert Andrich", "number": "8", "position": "MF", "nationality": "Germany"},
        {"name": "Exequiel Palacios", "number": "25", "position": "MF", "nationality": "Argentina"},
        {"name": "Aleix García", "number": "24", "position": "MF", "nationality": "Spain"},
        {"name": "Ibrahim Maza", "number": "30", "position": "MF", "nationality": "Algeria"},
        {"name": "Malik Tillman", "number": "10", "position": "MF", "nationality": "United States"},
        {"name": "Jonas Hofmann", "number": "7", "position": "MF", "nationality": "Germany"},
        {"name": "Eliesse Ben Seghir", "number": "17", "position": "FW", "nationality": "Morocco"},
        {"name": "Martin Terrier", "number": "11", "position": "FW", "nationality": "France"},
        {"name": "Ernest Poku", "number": "19", "position": "FW", "nationality": "Netherlands"},
        {"name": "Nathan Tella", "number": "23", "position": "FW", "nationality": "Nigeria"},
        {"name": "Montrell Culbreath", "number": "42", "position": "FW", "nationality": "Germany"},
        {"name": "Christian Kofane", "number": "35", "position": "FW", "nationality": "Cameroon"},
        {"name": "Patrik Schick", "number": "14", "position": "FW", "nationality": "Czech Republic"},
    ],
    "RB Leipzig": [
        {"name": "Maarten Vandevoordt", "number": "26", "position": "GK", "nationality": "Belgium"},
        {"name": "Péter Gulácsi", "number": "1", "position": "GK", "nationality": "Hungary"},
        {"name": "Leopold Zingerle", "number": "25", "position": "GK", "nationality": "Germany"},
        {"name": "Castello Lukeba", "number": "23", "position": "DF", "nationality": "France"},
        {"name": "El Chadaille Bitshiabu", "number": "5", "position": "DF", "nationality": "France"},
        {"name": "Willi Orbán", "number": "4", "position": "DF", "nationality": "Hungary"},
        {"name": "Lukas Klostermann", "number": "16", "position": "DF", "nationality": "Germany"},
        {"name": "David Raum", "number": "22", "position": "DF", "nationality": "Germany"},
        {"name": "Max Finkgräfe", "number": "35", "position": "DF", "nationality": "Germany"},
        {"name": "Ridle Baku", "number": "17", "position": "DF", "nationality": "Germany"},
        {"name": "Benjamin Henrichs", "number": "39", "position": "DF", "nationality": "Germany"},
        {"name": "Kosta Nedeljkovic", "number": "19", "position": "DF", "nationality": "Serbia"},
        {"name": "Nicolas Seiwald", "number": "13", "position": "MF", "nationality": "Austria"},
        {"name": "Benno Kaltefleiter", "number": "37", "position": "MF", "nationality": "Germany"},
        {"name": "Assan Ouédraogo", "number": "20", "position": "MF", "nationality": "Germany"},
        {"name": "Ezechiel Banzuzi", "number": "6", "position": "MF", "nationality": "Netherlands"},
        {"name": "Xaver Schlager", "number": "24", "position": "MF", "nationality": "Austria"},
        {"name": "Christoph Baumgartner", "number": "14", "position": "MF", "nationality": "Austria"},
        {"name": "Brajan Gruda", "number": "10", "position": "MF", "nationality": "Germany"},
        {"name": "Andrija Maksimovic", "number": "33", "position": "MF", "nationality": "Serbia"},
        {"name": "Viggo Gebel", "number": "47", "position": "MF", "nationality": "Germany"},
        {"name": "Yan Diomande", "number": "49", "position": "FW", "nationality": "Cote d'Ivoire"},
        {"name": "Antonio Nusa", "number": "7", "position": "FW", "nationality": "Norway"},
        {"name": "Suleman Sani", "number": "18", "position": "FW", "nationality": "Nigeria"},
        {"name": "Tidiam Gomis", "number": "27", "position": "FW", "nationality": "France"},
        {"name": "Ayodele Thomas", "number": "21", "position": "FW", "nationality": "Netherlands"},
        {"name": "Johan Bakayoko", "number": "9", "position": "FW", "nationality": "Belgium"},
        {"name": "Rômulo", "number": "40", "position": "FW", "nationality": "Brazil"},
        {"name": "Conrad Harder", "number": "11", "position": "FW", "nationality": "Denmark"},
        {"name": "Samba Konaté", "number": "45", "position": "FW", "nationality": "France"},
    ],
    "Borussia Dortmund": [
        {"name": "Gregor Kobel", "number": "1", "position": "GK", "nationality": "Switzerland"},
        {"name": "Alexander Meyer", "number": "33", "position": "GK", "nationality": "Germany"},
        {"name": "Patrick Drewes", "number": "30", "position": "GK", "nationality": "Germany"},
        {"name": "Silas Ostrzinski", "number": "31", "position": "GK", "nationality": "Germany"},
        {"name": "Nico Schlotterbeck", "number": "4", "position": "DF", "nationality": "Germany"},
        {"name": "Waldemar Anton", "number": "3", "position": "DF", "nationality": "Germany"},
        {"name": "Luca Reggiani", "number": "49", "position": "DF", "nationality": "Italy"},
        {"name": "Ramy Bensebaini", "number": "5", "position": "DF", "nationality": "Algeria"},
        {"name": "Niklas Süle", "number": "25", "position": "DF", "nationality": "Germany"},
        {"name": "Emre Can", "number": "23", "position": "DF", "nationality": "Germany"},
        {"name": "Filippo Mane", "number": "39", "position": "DF", "nationality": "Italy"},
        {"name": "Daniel Svensson", "number": "24", "position": "DF", "nationality": "Sweden"},
        {"name": "Almugera Kabar", "number": "42", "position": "DF", "nationality": "Germany"},
        {"name": "Julian Ryerson", "number": "26", "position": "DF", "nationality": "Norway"},
        {"name": "Salih Özcan", "number": "6", "position": "MF", "nationality": "Türkiye"},
        {"name": "Felix Nmecha", "number": "8", "position": "MF", "nationality": "Germany"},
        {"name": "Jobe Bellingham", "number": "7", "position": "MF", "nationality": "England"},
        {"name": "Carney Chukwuemeka", "number": "17", "position": "MF", "nationality": "Austria"},
        {"name": "Marcel Sabitzer", "number": "20", "position": "MF", "nationality": "Austria"},
        {"name": "Yan Couto", "number": "2", "position": "MF", "nationality": "Brazil"},
        {"name": "Julian Brandt", "number": "10", "position": "MF", "nationality": "Germany"},
        {"name": "Karim Adeyemi", "number": "27", "position": "FW", "nationality": "Germany"},
        {"name": "Samuele Inácio", "number": "40", "position": "FW", "nationality": "Italy"},
        {"name": "Maximilian Beier", "number": "14", "position": "FW", "nationality": "Germany"},
        {"name": "Serhou Guirassy", "number": "9", "position": "FW", "nationality": "Guinea"},
        {"name": "Fábio Silva", "number": "21", "position": "FW", "nationality": "Portugal"},
    ],
    "FC Bayern München": [
        {"name": "Jonas Urbig", "number": "40", "position": "GK", "nationality": "Germany"},
        {"name": "Manuel Neuer", "number": "1", "position": "GK", "nationality": "Germany"},
        {"name": "Sven Ulreich", "number": "26", "position": "GK", "nationality": "Germany"},
        {"name": "Leon Klanac", "number": "48", "position": "GK", "nationality": "Germany"},
        {"name": "Dayot Upamecano", "number": "2", "position": "DF", "nationality": "France"},
        {"name": "Jonathan Tah", "number": "4", "position": "DF", "nationality": "Germany"},
        {"name": "Min-jae Kim", "number": "3", "position": "DF", "nationality": "Korea, South"},
        {"name": "Hiroki Ito", "number": "21", "position": "DF", "nationality": "Japan"},
        {"name": "Alphonso Davies", "number": "19", "position": "DF", "nationality": "Canada"},
        {"name": "Raphaël Guerreiro", "number": "22", "position": "DF", "nationality": "Portugal"},
        {"name": "Josip Stanisic", "number": "44", "position": "DF", "nationality": "Croatia"},
        {"name": "Konrad Laimer", "number": "27", "position": "DF", "nationality": "Austria"},
        {"name": "Aleksandar Pavlovic", "number": "45", "position": "MF", "nationality": "Germany"},
        {"name": "Joshua Kimmich", "number": "6", "position": "MF", "nationality": "Germany"},
        {"name": "David Santos Daiber", "number": "47", "position": "MF", "nationality": "Portugal"},
        {"name": "Tom Bischof", "number": "20", "position": "MF", "nationality": "Germany"},
        {"name": "Leon Goretzka", "number": "8", "position": "MF", "nationality": "Germany"},
        {"name": "Bara Sapoko Ndiaye", "number": "39", "position": "MF", "nationality": "Senegal"},
        {"name": "Jamal Musiala", "number": "10", "position": "MF", "nationality": "Germany"},
        {"name": "Lennart Karl", "number": "42", "position": "MF", "nationality": "Germany"},
        {"name": "Luis Díaz", "number": "14", "position": "FW", "nationality": "Colombia"},
        {"name": "Michael Olise", "number": "17", "position": "FW", "nationality": "France"},
        {"name": "Serge Gnabry", "number": "7", "position": "FW", "nationality": "Germany"},
        {"name": "Harry Kane", "number": "9", "position": "FW", "nationality": "England"},
        {"name": "Nicolas Jackson", "number": "11", "position": "FW", "nationality": "Senegal"},
    ],
}

if __name__ == "__main__":
    for club_name, players in CLUBS_DATA.items():
        safe_name = club_name.replace(" ", "_").replace("/", "_")
        filepath = os.path.join(DATA_DIR, f"{safe_name}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(players, f, ensure_ascii=False, indent=2)
        print(f"Saved {club_name}: {len(players)} players -> {filepath}")
    
    print(f"\nTotal clubs: {len(CLUBS_DATA)}")
    total = sum(len(p) for p in CLUBS_DATA.values())
    print(f"Total players: {total}")
