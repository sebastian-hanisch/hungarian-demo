"""Konstanten, Regler-Grenzen, Presets und feste Seed-Mengen der Demo "Ungarische Methode"."""

# --- Regler (wie in den beiden Vorgängerdemos) ---------------------------------------------------------------------------------
N_MIN, N_MAX, DEFAULT_N = 3, 40, 20          # Fahrzeuge
M_MIN, M_MAX, DEFAULT_M = 3, 40, 20          # Aufträge
REACH_MIN, REACH_MAX, DEFAULT_REACH = 10, 150, 40   # Reichweite in Minuten; ab 142 ist auf der 100x100-Karte alles erreichbar
BALLUNG_MIN, BALLUNG_MAX, DEFAULT_BALLUNG = 0, 100, 0   # ganze Prozent, Schritt 25
DEFAULT_SEED = 165
SEED_MAX = 2_000_000_000

NETS = {"random": "Zufällige Karte", "steal": "Billigste Kante klaut (2×2)", "p4": "Pfad aus vier Punkten", "paths": "Drei Pfade hintereinander", "chain": "Lange Kette (13 Kanten)"}
DEFAULT_NET = "random"
FIXED_NETS = ("steal", "p4", "paths", "chain")

VIEW_LABELS = {"prices": "Preise", "paths": "Kürzeste Wege"}
DEFAULT_VIEW = "prices"

# --- feste Seed-Mengen (dieselben wie in den Vorgängerdemos; unabhängig vom Nutzer-Seed) --------------------------------------------
DIST_SEEDS = tuple(range(100000, 100100))
SWEEP_SEEDS = DIST_SEEDS[:40]
REACH_SWEEP = (10, 15, 20, 25, 30, 40, 50, 60, 80, 100, 120, 150)
SCALE_NS = (10, 20, 40, 80, 160, 320)      # Aufwand-Experiment: Fahrzeuge = Aufträge, mittlerer Grad konstant (Reichweite ~ 1/sqrt(n))
SCALE_SEEDS = DIST_SEEDS[:10]
SCALE_REACH_AT_20 = 40

COLORS = {"matched": "#1f77b4", "add": "#2ca02c", "drop": "#d62728", "common": "#8c8c8c", "vehicle": "#111111", "order": "#ff7f0e", "cover": "#9467bd", "optimal": "#d62728",
          "tight": "#444444", "hungarian": "#d62728"}

# --- Presets ------------------------------------------------------------------------------------------------------------------
_BASE = dict(net="random", view=DEFAULT_VIEW, n=DEFAULT_N, m=DEFAULT_M, reach=DEFAULT_REACH, ballung=DEFAULT_BALLUNG, seed=DEFAULT_SEED)
PRESETS = {
    "⚖️ Die billigste Kante klaut": {**_BASE, "net": "steal"},
    "🔗 Pfad aus vier Punkten": {**_BASE, "net": "p4"},
    "⛓️ Lange Kette": {**_BASE, "net": "chain"},
    "🗺️ Mittlere Reichweite": {**_BASE},
    "🌐 Alles erreichbar": {**_BASE, "reach": 150, "seed": 316},
    "📡 Knappe Reichweite": {**_BASE, "reach": 10, "seed": 33},
    "🧮 Große Karte": {**_BASE, "n": 40, "m": 40, "reach": 60, "seed": 58},
    "🛣️ Kürzeste-Wege-Sicht": {**_BASE, "view": "paths"},
}
# Jede Zahl in diesen Texten ist in tests/test_claims.py über die 100 festen Karten (DIST_SEEDS) belegt
PRESET_HELP = {
    "⚖️ Die billigste Kante klaut": "Greedy und Verbesserungswege zahlen 18 Minuten. Die Ungarische Methode wählt in Runde 1 die billigste Kante (4 Minuten), tauscht sie in Runde 2 wieder aus und kommt auf 10 Minuten: die Grenzkosten der beiden Paare sind 4 und 6.",
    "🔗 Pfad aus vier Punkten": "Beide Greedy-Regeln finden 1 Paar. Die Ungarische Methode wählt erst die billige Mittelkante (2 Minuten), gibt sie in Runde 2 wieder frei und hat 2 Paare für 20 Minuten: das zweite Paar kostet 18 Minuten zusätzlich.",
    "⛓️ Lange Kette": "Die ersten sechs Paare kosten je 2 Minuten zusätzlich, das siebte 58: „Paare zuerst“ heißt hier, für ein Paar 58 Minuten mehr zu zahlen (zusammen 70).",
    "🗺️ Mittlere Reichweite": "Auf allen 100 Karten (20 Fahrzeuge, 20 Aufträge, Reichweite 40) hat die Ungarische Methode das Optimum: Mehrkosten 0, wo die Verbesserungswege im Median 8 % (ab Greedy) und 36 % (ab leer) über dem Optimum liegen. Der Preis: 1 698 statt 140 durchsuchte Kanten, rund 12-mal so viele.",
    "🌐 Alles erreichbar": "Greedy bedient alle Aufträge schon, die Verbesserungswege tun nichts: beide liegen im Median 14 % über dem Optimum, ab leerem Start über 150 %. Die Ungarische Methode findet das Optimum und durchsucht dafür 5 322 Kanten bei 400 Kanten im Netz, rund 13-mal so viele.",
    "📡 Knappe Reichweite": "Hier reicht Greedy: auf 80 von 100 Karten hat es schon die größtmögliche Paarzahl, und die Verbesserungswege sind im Median schon optimal (Mehrkosten 0). Die Ungarische Methode ist auch hier optimal, durchsucht aber 51 Kanten bei 11 Kanten im Netz (Verbesserungswege ab Greedy: 3).",
    "🧮 Große Karte": "Bei 40 Fahrzeugen und 40 Aufträgen durchsucht die Ungarische Methode im Mittel 21 124 Kanten, die Verbesserungswege ab Greedy 393: rund 54-mal so viele - dafür Mehrkosten 0 statt im Median 18 %.",
    "🛣️ Kürzeste-Wege-Sicht": "Dieselbe Karte wie „Mittlere Reichweite“, aber als Dijkstra: jede Runde ist ein kürzester Weg auf reduzierten Kosten, und der Preis eines Auftrags steigt um genau min(Abstand, Abstand zum Ziel) - Johnsons Umgewichtung, nach jedem Umklappen neu gepflegt.",
}
