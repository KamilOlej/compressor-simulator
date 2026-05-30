# Symulator napełniania butli sprężarką

> **Politechnika Koszalińska 2025**  
> Autorzy: Arkadisz Szwed, Kamil Olejniczak

Aplikacja desktopowa w Pythonie symulująca napełnianie butli sprężonym gazem z automatycznym sterownikiem rozmytym (logika Mamdaniego).

---

## Spis treści

- [Opis projektu](#opis-projektu)
- [Funkcjonalności](#funkcjonalności)
- [Wymagania](#wymagania)
- [Uruchomienie](#uruchomienie)
- [Kompilacja do pliku wykonywalnego](#kompilacja-do-pliku-wykonywalnego)
- [Struktura projektu](#struktura-projektu)
- [Sterownik rozmyty](#sterownik-rozmyty)
- [Bezpieczeństwo](#bezpieczeństwo)
- [Powiązanie z JIRA](#powiązanie-z-jira)
- [Licencja](#licencja)

---

## Opis projektu

Aplikacja zastępuje fizyczne stanowisko laboratoryjne do badania procesu napełniania butli sprężarką. Sterownik rozmyty reguluje otwarcie zaworu proporcjonalnie do błędu między ciśnieniem zadanym a aktualnym.

**Zakres ciśnienia:** 0 – 300 bar (hard limit z automatycznym odcięciem).

## Funkcjonalności

| Funkcja | Opis |
|---|---|
| Podłączanie sprężarki / butli | Toggle z wizualną informacją (zielony/czerwony) |
| Wartość zadana | Suwak 0–300 bar |
| Napełnianie | Start/stop z walidacją połączeń |
| Odcięcie | Natychmiastowe zatrzymanie |
| Awaryjne odcięcie | Blokada do ręcznego resetu |
| Sterownik rozmyty | 5 reguł, defuzzyfikacja COG |
| Log bezpieczeństwa | Plik `safety_log.txt` z timestampami |
| Log UI | Eksport dziennika zdarzeń do `ui_log.txt` |

## Wymagania

- Python 3.8+
- `numpy`
- `tkinter` (wbudowany w Python z python.org)

```bash
pip install numpy
```

> **macOS:** Do poprawnego działania tkinter zalecany Python z [python.org](https://www.python.org/downloads/) lub ActiveTcl.

## Uruchomienie

```bash
git clone https://github.com/<twoj-login>/compressor-simulator.git
cd compressor-simulator
pip install numpy
python3 compressor_app_pl.py
```

## Kompilacja do pliku wykonywalnego

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install pyinstaller numpy
pyinstaller --onefile --windowed compressor_app_pl.py
# Wynik: dist/compressor_app_pl
```

### Windows

```bash
python -m venv venv
venv\Scripts\activate
pip install pyinstaller numpy
pyinstaller --onefile --windowed compressor_app_pl.py
# Wynik: dist\compressor_app_pl.exe
```

## Struktura projektu

```
compressor-simulator/
├── compressor_app_pl.py      # Główny plik aplikacji
├── README.md
├── .gitignore
├── CONTRIBUTING.md
├── docs/
│   ├── SRS.md                # Specyfikacja wymagań (IEEE 830)
│   ├── ARCHITECTURE.md       # Architektura i opis modułów
│   └── fuzzy_logic.md        # Szczegóły sterownika rozmytego
├── safety_log.txt            # Generowany automatycznie (nie commitować)
└── ui_log.txt                # Generowany przez użytkownika (nie commitować)
```

## Sterownik rozmyty

Algorytm Mamdaniego z 5 regułami lingwistycznymi:

| Reguła | Błąd (wejście) | Zawór (wyjście) |
|---|---|---|
| R1 | VNEG (≤ −150 bar) | SHUT (0%) |
| R2 | NEG (−200..0 bar) | SMALL (25%) |
| R3 | ZERO (−30..30 bar) | MEDIUM (50%) |
| R4 | POS (0..200 bar) | LARGE (75%) |
| R5 | VPOS (≥ 150 bar) | FULL (100%) |

Defuzzyfikacja: **COG (Center of Gravity)** na siatce 401 punktów.

Szczegółowy opis: [`docs/fuzzy_logic.md`](docs/fuzzy_logic.md)

## Bezpieczeństwo

- Ciśnienie ≥ 300 bar → auto-stop napełniania + wpis w `safety_log.txt`
- Awaryjne odcięcie blokuje start napełniania do ręcznego resetu
- Pętla sterowania sprawdza stan awarii co 200 ms

## Powiązanie z JIRA

Projekt dokumentowany w JIRA Scrum: [kompresor.atlassian.net](https://kompresor.atlassian.net/jira/software/projects/SCRUM/summary)

Konwencja commitów powiązanych z ticketami:
```
SCRUM-<numer>: krótki opis zmiany
```

Przykład:
```
SCRUM-3: Dodano defuzzyfikację COG dla błędu > 150 bar
```

## Licencja

Projekt akademicki – Politechnika Koszalińska 2025. Wszelkie prawa zastrzeżone.
