# Sterownik rozmyty – dokumentacja techniczna

**Projekt:** Symulator napełniania butli  
**Typ sterownika:** Mamdani  
**Plik:** `compressor_app_pl.py`

---

## Przegląd algorytmu

```
error = setpoint − pressure
  ↓
fuzzify_error(error)          → stopnie przynależności dla 5 zmiennych
  ↓
infer_valve(fuzzy_error)      → agregacja wyjść (MAX clipping)
  ↓
defuzzify_cog(y, agg)         → skalarna wartość otwarcia zaworu [0..1]
```

---

## Funkcje przynależności wejścia (błąd)

Dziedzina: `−300 .. +300 bar`  
Typ funkcji: trójkątna (`tri_mf(x, a, b, c)`)

| Zmienna | a | b (szczyt) | c | Interpretacja |
|---|---|---|---|---|
| VNEG | −300 | −300 | −150 | Bardzo duże niedociśnienie |
| NEG | −200 | −100 | 0 | Niedociśnienie |
| ZERO | −30 | 0 | 30 | Błąd bliski zeru |
| POS | 0 | 100 | 200 | Niedopełnienie (ciśnienie za niskie) |
| VPOS | 150 | 300 | 300 | Bardzo duże niedopełnienie |

### Wykres MF wejścia

```
μ
1.0 |*    *         *              *         *
    | \  / \       / \            / \       /
    |  \/   \     /   \          /   \     /
    |        \   /     \        /     \   /
0.0 +─────────────────────────────────────────→ błąd [bar]
   -300     -200  -100   0    100    200   300
    VNEG     NEG        ZERO  POS         VPOS
```

---

## Funkcje przynależności wyjścia (otwarcie zaworu)

Dziedzina: `0.0 .. 1.0`  
Typ funkcji: trójkątna

| Zmienna | a | b (szczyt) | c | Otwarcie zaworu |
|---|---|---|---|---|
| SHUT | 0.00 | 0.00 | 0.20 | ~0% |
| SMALL | 0.05 | 0.25 | 0.45 | ~25% |
| MEDIUM | 0.30 | 0.50 | 0.70 | ~50% |
| LARGE | 0.55 | 0.75 | 0.95 | ~75% |
| FULL | 0.80 | 1.00 | 1.00 | ~100% |

---

## Baza reguł

```
R1: JEŻELI error = VNEG  TO valve = SHUT    (ciśnienie za wysokie → zamknij)
R2: JEŻELI error = NEG   TO valve = SMALL   (lekkie przekroczenie → mały przepływ)
R3: JEŻELI error = ZERO  TO valve = MEDIUM  (zbliżone do setpoint → połowa)
R4: JEŻELI error = POS   TO valve = LARGE   (spore niedopełnienie → duży przepływ)
R5: JEŻELI error = VPOS  TO valve = FULL    (duże niedopełnienie → pełny przepływ)
```

---

## Metoda wnioskowania

### 1. Fuzzyfikacja

```python
def fuzzify_error(e):
    mfs = input_mfs()
    return {name: tri_mf(e, *params) for name, params in mfs.items()}
```

Zwraca słownik `{nazwa: stopień_przynależności}` dla każdej zmiennej lingwistycznej.

### 2. Aktywacja reguł i agregacja

```python
for in_term, out_term in RULES:
    degree = fuzzy_error.get(in_term, 0.0)   # stopień aktywacji reguły
    clipped = min(mf_output, degree)           # clipping (Mamdani)
    aggregated = max(aggregated, clipped)      # agregacja MAX
```

Siatka agregacji: 401 punktów równomiernie rozłożonych na [0, 1].

### 3. Defuzzyfikacja COG

```python
def defuzzify_cog(y, agg):
    num = sum(y * agg)
    den = sum(agg)
    return num / den if den != 0 else 0.0
```

---

## Przykład obliczeniowy

**Dane:** setpoint = 240 bar, ciśnienie = 120 bar

```
error = 240 − 120 = 120 bar

Fuzzyfikacja:
  VNEG = tri_mf(120, −300, −300, −150) = 0.000
  NEG  = tri_mf(120, −200, −100,    0) = 0.000
  ZERO = tri_mf(120,  −30,    0,   30) = 0.000
  POS  = tri_mf(120,    0,  100,  200) = 0.800   ← aktywna
  VPOS = tri_mf(120,  150,  300,  300) = 0.000

Aktywna reguła: R4 → LARGE (a=0.55, b=0.75, c=0.95), clipping na 0.8

Defuzzyfikacja COG → valve = 0.75 → 75% otwarcia
```

---

## Powiązanie z kodem

| Funkcja | Linia (przybliżona) | Opis |
|---|---|---|
| `tri_mf` | ~21 | Trójkątna funkcja przynależności |
| `input_mfs` | ~31 | Definicja MF wejścia |
| `output_mfs` | ~40 | Definicja MF wyjścia |
| `RULES` | ~49 | Baza reguł (lista krotek) |
| `fuzzify_error` | ~57 | Fuzzyfikacja błędu |
| `infer_valve` | ~61 | Wnioskowanie + agregacja |
| `defuzzify_cog` | ~73 | Defuzzyfikacja COG |
| `background_loop` | ~254 | Wywołanie pełnego łańcucha co 200 ms |
