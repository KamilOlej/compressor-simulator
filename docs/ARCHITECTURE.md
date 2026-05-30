# Architektura aplikacji

## Diagram komponentów

```
compressor_app_pl.py
│
├── Moduł: Funkcje rozmyte (top-level)
│   ├── tri_mf(x, a, b, c)
│   ├── input_mfs()
│   ├── output_mfs()
│   ├── RULES
│   ├── fuzzify_error(e)
│   ├── infer_valve(fuzzy_error)
│   └── defuzzify_cog(y, agg)
│
├── Moduł: System logowania (top-level)
│   ├── append_safety_log(msg)
│   └── reset_safety_log()
│
└── Klasa: CompressorApp
    ├── __init__(root)          → GUI setup + wątek
    ├── Sterowanie urządzeniami
    │   ├── toggle_compressor()
    │   └── toggle_cylinder()
    ├── Sterowanie napełnianiem
    │   ├── toggle_filling()
    │   ├── cutoff()
    │   ├── emergency_cutoff()
    │   └── reset_emergency()
    ├── Obsługa UI
    │   ├── on_setpoint_change()
    │   ├── randomize_pressure()
    │   ├── log(msg)
    │   ├── update_ui()
    │   ├── update_fuzzy_ui(err, valve)
    │   ├── save_ui_log()
    │   ├── reset_safety_log_ui()
    │   └── show_info()
    └── Pętla tła
        ├── background_loop()   → threading.Thread (daemon)
        └── on_close()          → stop wątku + destroy
```

## Przepływ danych – napełnianie

```
Użytkownik (suwak setpoint)
        │
        ▼
    setpoint [bar]
        │
        ├──► error = setpoint − pressure
        │
        ▼
  fuzzify_error(error)
        │
        ▼
  infer_valve(fuzzy_error)   ←── RULES (5 reguł)
        │
        ▼
  defuzzify_cog(y, agg) → valve ∈ [0, 1]
        │
        ▼
  pressure += valve × scale + noise
        │
        ▼
  update_ui()  →  GUI (label, status)
```

## Wątek tła

```python
threading.Thread(target=self.background_loop, daemon=True)
```

- Działa niezależnie od wątku GUI
- Komunikacja z GUI wyłącznie przez `root.after(0, callback)` (thread-safe)
- Częstotliwość: 200 ms (5 Hz)
- Zatrzymywany flagą `_stop_thread` przy zamknięciu okna

## Pliki generowane przez aplikację

| Plik | Kiedy tworzony | Zawartość |
|---|---|---|
| `safety_log.txt` | Przy pierwszym zdarzeniu bezpieczeństwa | Zdarzenia awaryjne z timestampem |
| `ui_log.txt` | Na żądanie użytkownika | Kopia logu z widżetu Text |
