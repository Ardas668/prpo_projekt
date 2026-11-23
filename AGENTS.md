# Pravidla a metodika asistenta (AGENTS.md)

Tento dokument definuje lokální pravidla, metodiku a mantinely pro AI asistenta při práci na semestrálním projektu v tomto repozitáři.

---

## 1. O co v projektu jde

Jde o vývoj informačního systému pro vzdělávací centrum (Akademie Trutnov) v rámci předmětu **Pokročilé programování (PPRO)** na FIM UHK (ZS 2026/2027). Aplikace pokrývá správu kurzů, termínů, lektorů, účastníků, nepřekročitelných kapacit, pořadníku zájemců, docházky a vydávání unikátních osvědčení.

Kompletní zadání, detailní funkční požadavky, obchodní pravidla, otevřené otázky a záznamy architektonických rozhodnutí jsou uvedeny v technické dokumentaci:
👉 **[README.md](./README.md)** *(informace zde neduplikujeme)*.

---

## 2. Klíčové pravidlo: Explicitní schvalování postupů vývojářem

> [!IMPORTANT]
> **Asistent NIKDY neprovádí žádné netriviální kroky, architektonická rozhodnutí ani generování rozsáhlého kódu samostatně bez předchozího explicitního souhlasu vývojáře.**

* Každý krok (výběr technologického stacku, návrh datového modelu, zavedení vrstev, implementace doménové logiky, volba knihoven atd.) musí asistent nejprve **strukturovaně předložit** jako návrh.
* Návrh musí obsahovat:
  1. Cíl daného kroku.
  2. Variantní řešení s výhodami a nevýhodami.
  3. Doporučení asistenta s věcným zdůvodněním.
* Asistent pokračuje v exekuci **až po výslovném schválení vývojářem** (např. „Souhlasím s variantou A“, „Schváleno“, „Pokračuj“).

---

## 3. Metodika a pracovní postupy

1. **Inkrementální postup po malých krocích:**
   * Žádné masivní monolity kódu najednou.
   * Postupovat po logických, snadno revidovatelných celcích (Analýza/Model → Databáze a migrace → Doménová logika a pravidla → API/Prezentace → Testy → Dockerizace).
2. **Průběžná evidence rozhodnutí:**
   * Jakmile se s vývojářem dohodne řešení otevřeného bodu nebo architektonický kompromis, asistent jej ihned zapíše do sekce `Rozhodnutí` v [README.md](./README.md) ve formátu ADR.
3. **Konzistence a integrita kódu:**
   * Striktní dodržování třívrstvé architektury s jednosměrnými závislostmi.
   * Zachování čistoty kódu, komentářů a konvencí.
4. **Git hygiena:**
   * Atomické commity odpovídající schváleným krokům s konvenčními zprávami (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`).
   * Žádné nechtěné nebo dočasné soubory v repozitáři.

---

## 4. Hranice a bezpečnostní pravidla

* **Data:** Výhradně syntetická data. Nikdy do repozitáře nevkládat reálné osobní údaje, soukromá data ze stáží/práce ani produkční přihlašovací údaje.
* **Tajemství a konfigurace:** Hesla, API klíče a spojení na databázi spravovat přes šablonu `.env.example` a environmentální proměnné, nikdy je necommitovat.
* **Testy:** Každé klíčové obchodní pravidlo (nepřekročení kapacity, FIFO pořadník, neměnnost osvědčení, dohledatelnost zrušených přihlášek) musí mít automatizovaný test.
* **Komunikace:** Odpovídat vždy maximálně stručně, přímočaře a věcně bez zbytečného textového balastu.
