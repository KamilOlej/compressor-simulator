# Specyfikacja Wymagań Oprogramowania (SRS)
## Symulator napełniania butli sprężarką

**Standard:** IEEE 830-1998  
**Wersja dokumentu:** 1.0  
**Data:** 2025  
**Autorzy:** Arkadisz Szwed, Kamil Olejniczak  
**Uczelnia:** Politechnika Koszalińska  
**Projekt JIRA:** [SCRUM](https://kompresor.atlassian.net/jira/software/projects/SCRUM/summary)

---

## 1. Wprowadzenie

### 1.1 Cel dokumentu

Dokument określa wymagania funkcjonalne i niefunkcjonalne aplikacji symulującej proces napełniania butli sprężonym gazem z automatycznym sterownikiem rozmytym. Stanowi podstawę do weryfikacji i odbioru projektu.

### 1.2 Zakres systemu

System o nazwie **Symulator napełniania butli (PL)** umożliwia:

- Symulację procesu napełniania butli sprężarką w środowisku desktopowym
- Automatyczne sterowanie zaworem za pomocą sterownika rozmytego (logika Mamdaniego)
- Monitorowanie ciśnienia i stanu urządzeń w czasie rzeczywistym
- Rejestrację zdarzeń bezpieczeństwa w pliku logu

System **nie** obejmuje:
- Sterowania rzeczywistym sprzętem (tylko symulacja)
- Komunikacji sieciowej
- Wielodostępu / autoryzacji użytkownika

### 1.3 Definicje i skróty

| Termin | Definicja |
|---|---|
| Butla | Wirtualny zbiornik ciśnieniowy, zakres 0–300 bar |
| Sprężarka | Wirtualne źródło ciśnienia |
| Zawór | Regulowany element sterujący przepływem (0–100%) |
| Błąd (error) | Różnica: wartość_zadana − ciśnienie_aktualne [bar] |
| COG | Center of Gravity – metoda defuzzyfikacji |
| MF | Membership Function – funkcja przynależności |
| GUI | Graphical User Interface |
| SRS | Software Requirements Specification |

### 1.4 Odniesienia

- IEEE Std 830-1998 – Recommended Practice for Software Requirements Specifications
- Dokumentacja projektu JIRA: SCRUM Epic
- Kod źródłowy: `compressor_app_pl.py`

---

## 2. Opis ogólny systemu

### 2.1 Perspektywa produktu

Aplikacja standalone uruchamiana lokalnie. Nie wymaga połączenia sieciowego. Interfejs desktopowy oparty na bibliotece tkinter.

```
┌─────────────────────────────────────────────────────┐
│                    Użytkownik                       │
└──────────────────────┬──────────────────────────────┘
                       │ GUI (tkinter)
┌──────────────────────▼──────────────────────────────┐
│              CompressorApp (GUI Layer)               │
├─────────────────────┬───────────────────────────────┤
│  Sterownik rozmyty  │     Symulacja ciśnienia        │
│  (Fuzzy Controller) │     (background thread)        │
├─────────────────────┴───────────────────────────────┤
│              System plików (logi)                    │
│         safety_log.txt | ui_log.txt                 │
└─────────────────────────────────────────────────────┘
```

### 2.2 Funkcje produktu (podsumowanie)

- **F01** Podłączanie/odłączanie sprężarki i butli
- **F02** Ustawianie wartości zadanej ciśnienia (0–300 bar)
- **F03** Start/stop procesu napełniania
- **F04** Automatyczne sterowanie zaworem sterownikiem rozmytym
- **F05** Odcięcie manualne i awaryjne
- **F06** Wyświetlanie aktualnego ciśnienia i stanu sterownika
- **F07** Rejestracja zdarzeń bezpieczeństwa
- **F08** Eksport logu UI

### 2.3 Charakterystyka użytkownika

Docelowy użytkownik: student/pracownik uczelni technicznej. Zakładana znajomość podstawowych pojęć z zakresu automatyki i systemów pneumatycznych.

### 2.4 Ograniczenia ogólne

- Platforma: Windows 10+, macOS 11+, Linux (Ubuntu 20.04+)
- Język: Python 3.8+
- Brak wymagań sprzętowych poza standardowym komputerem

---

## 3. Wymagania funkcjonalne

### F01 – Podłączanie urządzeń

**ID:** SCRUM-2  
**Priorytet:** Wysoki

| Atrybut | Wartość |
|---|---|
| Wejście | Kliknięcie przycisku Sprężarka / Butla |
| Przetwarzanie | Zmiana stanu: odłączona ↔ podłączona |
| Wyjście | Zmiana koloru przycisku (czerwony / zielony), wpis w logu UI |
| Warunek błędu | Brak – zawsze wykonywalne |

### F02 – Ustawianie wartości zadanej

**ID:** SCRUM-2  
**Priorytet:** Wysoki

| Atrybut | Wartość |
|---|---|
| Wejście | Suwak (slider) w zakresie 0–300 bar |
| Przetwarzanie | Aktualizacja zmiennej `setpoint` co zdarzenie suwaka |
| Wyjście | Etykieta "Zadane: X.X bar" |

### F03 – Napełnianie butli

**ID:** SCRUM-5  
**Priorytet:** Wysoki

**Warunki wstępne:**
- Sprężarka podłączona
- Butla podłączona
- Brak aktywnej awarii

**Przepływ:**
1. Użytkownik klika „Rozpocznij napełnianie"
2. System weryfikuje warunki wstępne
3. Jeśli niespełnione → komunikat ostrzeżenia (messagebox)
4. Jeśli spełnione → `filling = True`, zmiana koloru przycisku
5. Pętla tła (co 200 ms) zwiększa ciśnienie proporcjonalnie do otwarcia zaworu

**Wzór przyrostu ciśnienia:**
```
increase = valve_opening × 1.0
scale    = min(1.0, (setpoint − pressure) / 40.0)
pressure += increase × scale + noise(−0.03, +0.03)
```

### F04 – Sterownik rozmyty

**ID:** SCRUM-4  
**Priorytet:** Wysoki

Opis szczegółowy w [`docs/fuzzy_logic.md`](fuzzy_logic.md).

Algorytm wywoływany co 200 ms w pętli tła:
1. Oblicz `error = setpoint − pressure`
2. Fuzzyfikuj błąd (5 funkcji MF trójkątnych)
3. Wnioskuj wg bazy reguł (5 reguł)
4. Agreguj wyjście (MAX)
5. Defuzzyfikuj (COG) → `valve ∈ [0, 1]`

### F05 – Odcięcie i awaria

**ID:** SCRUM-6  
**Priorytet:** Krytyczny

| Tryb | Wyzwalacz | Skutek | Reset |
|---|---|---|---|
| Odcięcie | Przycisk „Odcięcie" | `filling = False` | Automatyczny |
| Awaryjne odcięcie | Przycisk „Awaryjne odcięcie" | `filling = False`, `emergency = True` | Ręczny przycisk |
| Auto-stop | Ciśnienie ≥ 300 bar | `filling = False`, wpis w safety_log | Automatyczny |

### F06 – Wyświetlanie stanu

**ID:** SCRUM-5  
**Priorytet:** Średni

Odświeżanie co 200 ms (wywołanie `root.after(0, ...)`):
- Aktualne ciśnienie [bar] – dokładność 0.01 bar
- Stan butli (Podłączona / Niepodłączona)
- Błąd sterownika [bar]
- Otwarcie zaworu [%]

### F07 – Log bezpieczeństwa

**ID:** SCRUM-6  
**Priorytet:** Wysoki

- Plik: `safety_log.txt` w katalogu aplikacji
- Format: `[YYYY-MM-DD HH:MM:SS] treść zdarzenia`
- Zdarzenia logowane: awaryjne odcięcie, reset awarii, auto-stop przy 300 bar, zapis logu UI
- Reset logu: dostępny z GUI

### F08 – Eksport logu UI

**ID:** SCRUM-5  
**Priorytet:** Niski

- Plik: `ui_log.txt`
- Zawartość: wszystkie wpisy z widżetu Text w GUI
- Wyzwalacz: przycisk „Zapisz log do pliku"

---

## 4. Wymagania niefunkcjonalne

### 4.1 Wydajność

| ID | Wymaganie |
|---|---|
| NF-P01 | Pętla sterowania aktualizuje UI z częstotliwością ≥ 5 Hz (co 200 ms) |
| NF-P02 | Czas odpowiedzi GUI na akcję użytkownika: < 100 ms |
| NF-P03 | Zużycie pamięci RAM: < 100 MB |

### 4.2 Niezawodność

| ID | Wymaganie |
|---|---|
| NF-R01 | Wątek tła nie może blokować GUI (daemon thread) |
| NF-R02 | Błąd w pętli tła logowany do konsoli, aplikacja kontynuuje działanie |
| NF-R03 | Ciśnienie nie może przekroczyć 300 bar (hard limit w kodzie) |

### 4.3 Użyteczność

| ID | Wymaganie |
|---|---|
| NF-U01 | Wszystkie etykiety i komunikaty w języku polskim |
| NF-U02 | Stan krytyczny (awaria) sygnalizowany kolorem czerwonym |
| NF-U03 | Stan normalny (podłączone, napełnianie) sygnalizowany kolorem zielonym |

### 4.4 Przenośność

| ID | Wymaganie |
|---|---|
| NF-PORT01 | Aplikacja uruchamia się na Windows 10+, macOS 11+, Ubuntu 20.04+ |
| NF-PORT02 | Plik wykonywalny generowany przez PyInstaller (--onefile --windowed) |

### 4.5 Bezpieczeństwo

| ID | Wymaganie |
|---|---|
| NF-S01 | Każde zdarzenie awaryjne zapisywane do pliku z timestampem |
| NF-S02 | Reset logu bezpieczeństwa dokumentowany wpisem w tym samym pliku |
| NF-S03 | Napełnianie niemożliwe bez podłączenia obu urządzeń |

---

## 5. Wymagania interfejsu

### 5.1 Interfejs użytkownika

Okno 840×480 px, układ dwukolumnowy:
- Lewa kolumna: sterowanie (przyciski, suwak)
- Prawa kolumna: monitoring (ciśnienie, sterownik, dziennik)

### 5.2 Interfejs sprzętowy

Brak – aplikacja czysto softwarowa.

### 5.3 Interfejs systemowy

| Zasób | Opis |
|---|---|
| System plików | Zapis `safety_log.txt` i `ui_log.txt` w katalogu aplikacji |
| Wątki | 1 wątek daemon (pętla sterowania) |

---

## 6. Wymagania dotyczące danych

### 6.1 Dane wejściowe

| Dane | Typ | Zakres |
|---|---|---|
| Wartość zadana | float | 0.0 – 300.0 bar |
| Stan sprężarki | bool | True / False |
| Stan butli | bool | True / False |
| Stan awarii | bool | True / False |

### 6.2 Dane wyjściowe

| Dane | Typ | Opis |
|---|---|---|
| Ciśnienie aktualne | float | Wyświetlane, zaokrąglone do 2 miejsc |
| Otwarcie zaworu | float | 0.0–1.0 (wyświetlane jako %) |
| Błąd | float | setpoint − pressure |

---

## 7. Macierz śledzenia wymagań

| Wymaganie | Funkcja w kodzie | Ticket JIRA |
|---|---|---|
| F01 | `toggle_compressor`, `toggle_cylinder` | SCRUM-2 |
| F02 | `on_setpoint_change`, `sp_scale` | SCRUM-2 |
| F03 | `toggle_filling`, `background_loop` | SCRUM-5 |
| F04 | `fuzzify_error`, `infer_valve`, `defuzzify_cog` | SCRUM-4 |
| F05 | `cutoff`, `emergency_cutoff`, `reset_emergency` | SCRUM-6 |
| F06 | `update_ui`, `update_fuzzy_ui` | SCRUM-5 |
| F07 | `append_safety_log`, `reset_safety_log` | SCRUM-6 |
| F08 | `save_ui_log` | SCRUM-5 |

---

## 8. Kryteria akceptacji

| ID | Kryterium | Metoda weryfikacji |
|---|---|---|
| AC-01 | Ciśnienie nie przekracza 300 bar | Test automatyczny |
| AC-02 | Napełnianie blokowane bez podłączonych urządzeń | Test manualny |
| AC-03 | Awaryjne odcięcie zatrzymuje napełnianie natychmiast | Test manualny |
| AC-04 | Wpis w safety_log.txt przy każdym zdarzeniu awaryjnym | Inspekcja pliku |
| AC-05 | GUI reaguje na akcje w < 100 ms | Obserwacja wizualna |
| AC-06 | Sterownik rozmyty zwraca 75% otwarcia dla error=120 bar, setpoint=240 | Test obliczeniowy |
