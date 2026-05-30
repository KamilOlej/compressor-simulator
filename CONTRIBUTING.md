# Wytyczne dla współtwórców

## Konwencja gałęzi (Git Flow uproszczony)

```
main          ← stabilna wersja produkcyjna
develop       ← integracja zmian
feature/SCRUM-XX-opis   ← nowe funkcje
fix/SCRUM-XX-opis       ← poprawki błędów
```

## Konwencja commitów

Format: `<typ>(SCRUM-XX): krótki opis`

| Typ | Kiedy używać |
|---|---|
| `feat` | Nowa funkcjonalność |
| `fix` | Poprawka błędu |
| `docs` | Zmiany w dokumentacji |
| `refactor` | Refaktoryzacja bez zmiany zachowania |
| `test` | Dodanie / poprawa testów |
| `chore` | Zmiany konfiguracji, zależności |

**Przykłady:**
```
feat(SCRUM-3): dodano defuzzyfikację COG dla zakresu −300..300
fix(SCRUM-6): naprawiono zapis safety_log przy auto-stop
docs(SCRUM-2): zaktualizowano SRS sekcja 4.2
```

## Pull Request

1. Utwórz branch z `develop`: `git checkout -b feature/SCRUM-XX-opis develop`
2. Wprowadź zmiany, commituj wg konwencji
3. Otwórz PR do `develop` z opisem:
   - Co zostało zmienione
   - Numer ticketu JIRA
   - Kroki do przetestowania
4. PR wymaga przeglądu co najmniej jednego współautora

## Styl kodu

- PEP 8
- Komentarze i docstringi w języku polskim lub angielskim (spójnie w pliku)
- Maksymalna długość linii: 100 znaków
- Nazwy zmiennych: `snake_case`
- Nazwy klas: `PascalCase`
