"""Jede Zahl in den Hilfetexten, Presets, Tabellen und Grenzen der App ist hier über die 100 festen Karten (DIST_SEEDS) belegt.
Alles rechnet mit ganzen Zahlen und einem eigenen Zufallsgenerator - die Werte sind auf jeder Plattform dieselben; die Toleranzen decken nur die Rundung auf die im Text genannten Stellen.
Positive UND negative Aussagen: wo die Ungarische Methode gewinnt (Kosten), steht hier ebenso ein Test wie dort, wo sie verliert (Aufwand). Die Zahlen der Vorgängerstücke werden neu gemessen."""

import numpy as np
import pytest

import hu_constants as C
import hu_evaluation as ev
from hu_algorithm import hungarian
from hu_scenario import generate, long_chain, p4_chain, steal_2x2
from tests.test_algorithm import sequential_insertion


def near(value, expected, tol):
    assert abs(value - expected) <= tol, f"{value:.3f} statt {expected}"


def dist(n=20, m=20, reach=40, ballung=0):
    return ev.distribution(n, m, reach, ballung)


def median_gap(d, key="Verbesserungswege ab Greedy"):
    return float(np.median(d["gaps"][key]))


# --- feste Karten (Preset-Hilfe) ---------------------------------------------------------------------------------------------------------

def test_steal_2x2_numbers():
    res = hungarian(steal_2x2())
    assert res.cost == 10 and res.marginal == (4, 6)                                  # "10 Minuten ... Grenzkosten 4 und 6"
    assert ev.analyse(steal_2x2()).greedy["edge"].cost == 18 and ev.analyse(steal_2x2()).ap_edge.cost == 18      # "Greedy und Verbesserungswege zahlen 18 Minuten"


def test_p4_numbers():
    res = hungarian(p4_chain(1))
    a = ev.analyse(p4_chain(1))
    assert res.count == 2 and res.cost == 20 and res.marginal == (2, 18) and a.greedy["edge"].count == 1 == a.greedy["order"].count       # "1 Paar ... 2 Paare für 20 Minuten ... 18 zusätzlich"


def test_long_chain_numbers():
    res = hungarian(long_chain(6))
    assert res.marginal == (2, 2, 2, 2, 2, 2, 58) and res.cost == 70                # "sechs Paare je 2 ... das siebte 58 (zusammen 70)"


# --- Verteilungen über 100 Karten ------------------------------------------------------------------------------------------------------

def test_the_hungarian_method_is_optimal_on_every_map_at_every_reach():
    """Die zentrale positive Aussage: gleiche Paarzahl wie das Maximum und gleiche Kosten wie das Optimum - bei jeder Reichweite der Sweep-Reihe."""
    for reach in C.REACH_SWEEP:
        assert dist(reach=reach)["share_optimal"] == 1.0, reach


def test_mid_reach_numbers():
    d = dist()
    near(median_gap(d), 8.0, 0.5)                                                       # "Verbesserungswege im Median 8 % (ab Greedy)"
    near(median_gap(d, "Verbesserungswege ab leer"), 36.0, 0.5)                         # "und 36 % (ab leer)"
    near(median_gap(d, "Verbesserungswege ab Greedy, Tiefensuche"), 27.0, 0.6)
    near(d["scanned_mean"], 1698.0, 0.5)                                                # "1 698 ... durchsuchte Kanten"
    near(d["ap_edge_scanned_mean"], 140.0, 0.5)                                         # "statt 140"
    assert 11.5 <= d["scanned_mean"] / d["ap_edge_scanned_mean"] <= 12.5                # "rund 12-mal so viele"
    near(d["last_ratio_median"], 3.3, 0.05)                                             # letztes Paar gegen Durchschnitt
    assert d["share_greedy_max"] == pytest.approx(0.01)                                 # Greedy verliert auf 99 von 100 Karten Paare (Wurzel, neu gemessen)
    near(d["opt_pairs_mean"], 19.5, 0.05)                                               # 16,7 statt 19,5 (Wurzel, neu gemessen)
    near(d["greedy_pairs_mean"], 16.7, 0.05)


def test_all_reachable_numbers():
    d = dist(reach=150)
    near(d["scanned_mean"], 5322.0, 0.5)                                                # "5 322 Kanten"
    near(d["edges_mean"], 400.0, 1e-9)                                                  # "bei 400 Kanten im Netz"
    assert 12.5 <= d["scanned_mean"] / d["edges_mean"] <= 13.5                          # "rund 13-mal so viele"
    assert d["ap_edge_scanned_mean"] == 0.0 and d["share_greedy_max"] == 1.0            # "die Verbesserungswege tun nichts"
    near(median_gap(d), 14.0, 0.5)                                                      # "Greedy ... 14 % über dem Optimum"
    assert float(np.median(d["greedy_gaps"])) == pytest.approx(median_gap(d))           # Greedy und Verbesserungswege identisch
    assert median_gap(d, "Verbesserungswege ab leer") > 150.0                           # "ab leerem Start über 150 %"


def test_short_reach_numbers():
    d = dist(reach=10)
    assert d["share_greedy_max"] == pytest.approx(0.80)                                 # "auf 80 von 100 Karten ... größtmögliche Paarzahl"
    assert median_gap(d) == 0.0                                                         # "Verbesserungswege im Median schon optimal (Mehrkosten 0)"
    near(d["scanned_mean"], 51.0, 0.5)                                                  # "51 durchsuchte Kanten"
    near(d["edges_mean"], 11.0, 0.5)                                                    # "bei 11 Kanten im Netz"
    near(d["ap_edge_scanned_mean"], 3.0, 0.5)                                           # "Verbesserungswege ab Greedy: 3"
    assert d["scanned_mean"] > d["ap_edge_scanned_mean"]                                # auch hier mehr Aufwand (negativ)


def test_big_map_numbers():
    d = dist(40, 40, 60)
    near(d["scanned_mean"], 21124.0, 0.5)                                               # "21 124"
    near(d["ap_edge_scanned_mean"], 393.0, 0.5)                                         # "Verbesserungswege ab Greedy 393"
    assert 53.5 <= d["scanned_mean"] / d["ap_edge_scanned_mean"] <= 54.5                # "rund 54-mal so viele"
    near(median_gap(d), 18.0, 0.5)                                                      # "statt im Median 18 %"


def test_the_last_pair_is_the_expensive_one():
    """Grenzkosten steigen: das letzte Paar kostet im Median mehr als das Dreifache des Durchschnitts (Reichweite 40) - und die Kurve ist nie fallend."""
    assert dist()["last_ratio_median"] > 3.0
    for s in C.DIST_SEEDS[:20]:
        marg = hungarian(generate(20, 20, 40, 0, s), record=False).marginal
        assert list(marg) == sorted(marg)


def test_the_price_of_optimality_is_more_effort_at_every_reach():
    """Negative Aussage: die Ungarische Methode durchsucht bei jeder Reichweite mindestens so viele Kanten wie die Verbesserungswege ab Greedy (Sweep-Reihe, 40 Karten)."""
    for row in ev.reach_sweep(20, 20, 0):
        assert row["scanned"] > row["ap_scanned"], row["x"]


def test_scanned_edges_per_reach_have_a_peak_in_the_middle_for_the_baseline():
    """Text: 'bei knapper Reichweite gibt es wenig zu suchen, bei mittlerer und großer viel'."""
    rows = {r["x"]: r["scanned"] for r in ev.reach_sweep(20, 20, 0)}
    assert rows[10] < 0.1 * rows[40] and rows[150] > rows[40]


# --- Aufwand-Experiment ---------------------------------------------------------------------------------------------------------------------

def test_scaling_grows_about_quadratically_at_a_fixed_multiple_of_the_baseline():
    """Text: 'beide wachsen etwa mit dem Quadrat der Kartengröße; die Ungarische Methode bleibt bei einem festen Vielfachen der Verbesserungswege ab Greedy'."""
    rows = ev.scaling()
    ns = np.array([r["n"] for r in rows], dtype=float)
    for key in ("scanned", "ap_scanned"):
        slope = np.polyfit(np.log(ns), np.log([r[key] for r in rows]), 1)[0]
        assert 1.6 <= slope <= 2.2, key
    ratios = [r["scanned"] / r["ap_scanned"] for r in rows]
    assert min(ratios) >= 6.0 and max(ratios) <= 12.0                                    # ein festes Vielfaches (gemessen 6,9 bis 10,9)


# --- Negativkontrolle -------------------------------------------------------------------------------------------------------------------------

def test_sequential_insertion_fails_on_all_maps_with_more_vehicles_than_orders():
    """Zeilenweises Einfügen der größeren Seite (n = 20 Fahrzeuge, m = 10 Aufträge, Reichweite 40) ist auf allen 100 Karten falsch; die Ungarische Methode nie."""
    wrong = 0
    for s in C.DIST_SEEDS:
        sc = generate(20, 10, 40, 0, s)
        wrong += sequential_insertion(sc) != (hungarian(sc, record=False).count, hungarian(sc, record=False).cost)
    assert wrong == 100
