# Ungarische Methode – die billigste unter den größtmöglichen Zuordnungen – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-hungarian-demo.streamlit.app/)**

Drittes Stück der **Matching-Linie** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning", Fortsetzung der [Verbesserungswege-Demo](https://github.com/sebastian-hanisch/augmenting-path-demo):
anders als die Fall-Demos im Portfolio (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt diese Demo **ein** Verfahren – die **Ungarische Methode** (Successive Shortest Paths mit Potenzialen) – an einem wachsenden Beispiel.
Verbesserungswege machen die Paarzahl größtmöglich, sind aber **kostenblind**. Die Ungarische Methode klappt in jeder Runde den **billigsten** Verbesserungsweg um und hält dabei **Preise** für alle Fahrzeuge und Aufträge, die zeigen, warum kein billigeres Matching mit gleich vielen Paaren existiert.
Ziel ist lexikografisch: erst möglichst viele Paare, dann möglichst geringe Kosten – ohne große Strafzahl (Big-M), als kleinste Kosten je Flusswert.

**Zwei Sichten auf dieselbe Rechnung** (umschaltbar): **Preise** (Aufträge haben Preise, Fahrzeuge Gewinne, jede Runde hebt Preise an) und **Kürzeste Wege** (jede Runde ist ein Dijkstra auf reduzierten Kosten; das Potenzial steigt um min(Abstand, Abstand zum Ziel) – die Umgewichtung aus Johnsons Verfahren, nach jedem Umklappen neu gepflegt). Beide lesen dieselben Rundendaten, sind also immer synchron.

**Einordnung in die Reihe (die Kanten des Graphen):** dieses Stück behebt die Kostenblindheit der Verbesserungswege. Seine eigenen Schwächen sind die Ansatzpunkte der nächsten: die Rechnung ist zentral und braucht alle Kosten (**Auktionsalgorithmus**), es gibt nur zwei getrennte Seiten (**Blossom → Gewichteter Blossom**), Kosten statt Vorlieben (**Gale–Shapley**), alles ist vorab bekannt (**Online-Matching**).
```
greedy-matching-demo (Wurzel: eine gewählte Zuordnung bleibt)                     [gebaut]
  ├─ augmenting-path-demo (Verbesserungswege: Paare optimal, Kosten blind)        [gebaut]
  │    ├─ hopcroft-karp-demo (viele kürzeste Wege je Phase)                       [gebaut]
  │    ├─ hungarian-demo (Ungarische Methode: Paare zuerst, dann Kosten)           [dieses Stück]
  │    │    └─ auction-algorithm-demo (Auktionsalgorithmus: dezentral)             [gebaut]
  │    └─ blossom-demo (allgemeine Graphen: ungerade Kreise, Kontraktion)          [gebaut]
  │        └─ weighted-blossom-demo (Ungarisch + Blossom, Konvergenz)              [gebaut]
  ├─ Gale–Shapley → Stabile Mitbewohner, Krankenhaus-Zulassung, Top Trading Cycles, Nierentausch [gebaut]
  └─ online-matching-demo (Aufträge kommen nacheinander)                          [gebaut]
```

## Ergebnis (Zahlen aus den Tests)

Jede hier genannte Zahl ist in `tests/test_claims.py` über die 100 festen Karten (Seeds 100000–100099) belegt. Standard: 20 Fahrzeuge, 20 Aufträge, Reichweite 40. Die Zahlen der Vorgänger werden neu gemessen, nicht zitiert.

| Frage | Ergebnis |
|---|---|
| Ist das Ergebnis optimal? | ✅ Ja: Paarzahl größtmöglich **und** Kosten minimal auf allen 100 Karten bei jeder Reichweite der Sweep-Reihe; unabhängig gegen scipy, networkx (`max_weight_matching` mit größtmöglicher Paarzahl), Brute Force und `min_cost_flow` geprüft, dazu je Runde die Invarianten und der Beweis (Preise C1–C5 mit Kostenidentität). |
| Und die Verbesserungswege? | ✅ Die Mehrkosten von 8 % (ab Greedy) bzw. 36 % (ab leerem Start) im Median und 27 % mit Tiefensuche sind hier 0. |
| Was kostet das? | ❌ Aufwand: bei Reichweite 40 durchsucht die Ungarische Methode im Mittel 1 698 Kanten, die Verbesserungswege ab Greedy 140 – rund 12-mal so viele. Das gilt bei **jeder** Reichweite der Sweep-Reihe. |
| Alles erreichbar (Reichweite 150) | ⚠️ Greedy bedient schon alle Aufträge, die Verbesserungswege tun nichts (14 % Mehrkosten im Median, vom leeren Start über 150 %). Die Ungarische Methode repariert genau das – für 5 322 durchsuchte Kanten bei 400 Kanten im Netz (rund 13-fach). |
| Sehr knappe Reichweite (10) | ⚠️ Auf 80 von 100 Karten hat Greedy schon die größtmögliche Paarzahl und die Verbesserungswege sind im Median schon optimal; die Ungarische Methode ist auch hier optimal, aber mit 51 statt 3 durchsuchten Kanten (bei 11 Kanten im Netz) der teurere Weg. |
| Große Karte (40 × 40, Reichweite 60) | ❌ 21 124 durchsuchte Kanten gegen 393 für die Verbesserungswege ab Greedy (rund 54-fach); deren Mehrkosten liegen im Median bei 18 %. |
| Das letzte Paar | ✅ Die Grenzkosten steigen von Runde zu Runde (nie fallend, getestet); das letzte Paar kostet im Median mehr als das 3,3-Fache des Durchschnitts. Lange Kette: sechs Paare je 2 Minuten, das siebte 58 (zusammen 70) – Lehrbeispiel für „Paare zuerst“. |
| Die billigste Kante klaut (2 × 2) | ✅ Greedy und Verbesserungswege zahlen 18 Minuten, die Ungarische Methode 10 (Grenzkosten 4 und 6). |
| Wie wächst der Aufwand? | ⚠️ Bei konstantem mittleren Grad wächst die Zahl der durchsuchten Kanten von 10 auf 320 Fahrzeuge mit der Steigung ≈ 1,9 (doppelt-logarithmisch), also etwa quadratisch – wie bei den Verbesserungswegen, nur bei einem festen Vielfachen (7- bis 11-fach). Gezählt werden durchsuchte Kanten, nie Sekunden; die Heap-Operationen kommen mit einem Log-Faktor hinzu. |
| Zeilenweises Einfügen (Jonker–Volgenant) | ❌ Als Negativkontrolle: fügt man die größere Seite (20 Fahrzeuge, 10 Aufträge) Zeile für Zeile ein, ist das Ergebnis auf allen 100 Karten falsch – hier braucht man den Mehrfachstart von allen freien Fahrzeugen. |

## Was nicht funktioniert hat / Vorab-Hypothesen

- **„Von Greedy aus starten, um Runden zu sparen.“** Geht bei diesem Verfahren nicht: ohne gültige Potenziale gibt es kein Greedy-Warmstart-Matching; die Ungarische Methode beginnt immer bei null (deshalb gibt es hier keinen Start-Umschalter wie in der Vorgänger-Demo).
- **„Potenzial nur für festgelegte Ecken erhöhen.“** Verletzt die Dualzulässigkeit: alle nicht festgelegten Ecken müssen um den Abstand des Ziels steigen.
- Erwartet und bestätigt: die Ungarische Methode ist immer optimal und immer aufwendiger; der Preis der Optimalität ist gemessen, nicht geschätzt.

## Was die Demo zeigt

- **Die Ungarische Methode in Aktion:** Schritt-Slider und ▶️ über die Runden, umschaltbar zwischen den beiden Sichten; links der Zustand vor der Runde, rechts danach; am Ende der **Beweis** (Prüftabelle C1–C5 mit echten Zahlen und die Kostenidentität als Gleichung). Darunter die Grenzkostenkurve.
- **Optimal – und was kostet das?** Ergebnis gegen die Referenz, Vergleichstabelle (Greedy, Verbesserungswege in drei Varianten, Ungarisch), Verteilung über 100 feste Karten, Aufwandstabelle, Sweep über die Reichweite und Aufwand-Experiment auf Abruf.
- **Feste Lehrbuchkarten** (2 × 2, Pfad aus vier Punkten, lange Kette) und zufällige Karten; **Wo die Annahmen enden:** welches spätere Stück an welcher Schwäche ansetzt.

## Modell und Verfahren

- **Netz:** $s \to$ Fahrzeug (0) $\to$ Auftrag ($c$) $\to t$ (0), alle Kapazitäten 1; kleinste Kosten je Flusswert durch Successive Shortest Paths. Ein Umklappen entspricht einem Flussweg im Restgraphen (gewählte Paare als Rückkanten mit Kosten $-c$).
- **Potenziale:** $\pi_v,\pi_o,P$ mit $\pi_s=0$; reduzierte Kosten $r=w+\pi_a-\pi_b\ge 0$. Jede Runde: Mehrfachstart-Dijkstra von allen freien Fahrzeugen (Abstand 0), Abbruch beim ersten festgelegten freien Auftrag ($d_t$); Update $\pi_x \mathrel{+}= \min(d_x, d_t)$, $P \mathrel{+}= d_t$. Die Grenzkosten des neuen Paars sind $W=d_t+P_{alt}$, nicht fallend; die Gesamtkosten sind $\sum W$.
- **Invarianten je Runde** (getestet): reduzierte Kosten $\ge 0$; gewählte Kanten straff; freie Fahrzeuge $\pi=0$; freie Aufträge $\pi=P$; Kostenidentität $\text{Kosten}=\sum\pi_o-\sum\pi_v-(m-\nu)P$; Potenziale nur wachsend.
- **Beweis:** mit $a_i=\pi_i$, $b_j=P-\pi_j$: C1 gewählte Kanten straff, C2 $\pi_j-\pi_i\le c_{ij}$ auf allen möglichen Kanten, C3 freie Fahrzeuge $\pi=0$, C4 freie Aufträge $\pi=P$, C5 kein freier Auftrag erreichbar (Königsche Überdeckung wie im Vorgänger). C1–C4 sind Dualzulässigkeit; nach schwacher Dualität kostet jedes Matching gleicher Größe mindestens so viel.
- **Tie-Break:** im Heap $(\text{Abstand},\text{Art},\text{Index})$, Aufträge vor Fahrzeugen; die Wege sind tie-abhängig, deshalb werden nur (Paare, Kosten) verglichen, nie Kantenmengen.
- **Laufzeit:** $O(\nu\cdot(E+V\log V))$; gemessen als durchsuchte Fahrzeug→Auftrag-Kanten (dazu getrennt Rückkanten-Schritte und Heap-Operationen).

## Dateien

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche |
| `hu_constants.py` | Regler-Grenzen, Presets und Hilfetexte, feste Seed-Mengen |
| `hu_presets.py` | Permalink, Preset- und Zufalls-Seed-Logik (Standardmuster des Portfolios, kopiert) |
| `hu_scenario.py` | Karten, eigener Zufallsgenerator, feste Lehrbuchkarten (aus der Verbesserungswege-Demo kopiert) |
| `hu_greedy.py` | Greedy-Regeln und Referenz-Optimum (aus der Verbesserungswege-Demo kopiert, ohne Import) |
| `hu_augment.py` | Verbesserungswege des Vorgängers (kopiert, nur für den Vergleich in der App) |
| `hu_algorithm.py` | **Neu:** Ungarische Methode (Dijkstra mit Potenzialen), Rundenprotokoll, Beweis |
| `hu_evaluation.py` | Einordnung, Verdict, Vergleichstabelle, Verteilung über viele Karten, Aufwand |
| `hu_visualization.py` | Plotly-Abbildungen (Achsen gesperrt für Touch-Geräte; Bögen bei Punkten auf einer Geraden) |
| `tests/` | Algorithmus (Handfälle, Invarianten je Runde, scipy, networkx, Brute Force und `min_cost_flow` als Gegenprobe, Beweis mit Negativtest), Auswertung, Presets, belegte Zahlen, AppTest-Rauchtests |

Die Kopien der Vorgänger werden durch einen Test bewacht: dieselben Karten und Regeln müssen die Zahlen der Vorgänger reproduzieren. Alle Daten sind synthetisch; die Laufzeit braucht nur numpy, pandas, plotly und streamlit (scipy und networkx sind reine Testorakel).

## Lokal starten

```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\streamlit run app.py
```

## Tests ausführen

```bash
venv\Scripts\pip install -r requirements-dev.txt
venv\Scripts\python -m pytest tests -v
```

Die Logik rechnet ausschließlich mit ganzen Zahlen; die im Text genannten Anteile und Mediane sind deshalb auf jeder Plattform identisch.
Die CI (`.github/workflows/tests.yml`) läuft auf Ubuntu mit Python 3.12, bei jedem Push und wöchentlich mit den jeweils neuesten Bibliotheksversionen.
