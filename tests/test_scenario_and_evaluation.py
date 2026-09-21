"""Auswertung: Einordnung, Verdict, Vergleichstabelle, Verteilung über viele Karten, Aufwandstabelle, Reichweite-Sweep, Aufwand-Experiment."""

import numpy as np
import pytest

import hu_constants as C
import hu_evaluation as ev
from hu_greedy import Matching
from hu_scenario import build, generate, long_chain, p4_chain, steal_2x2


def test_build_fixed_nets_ignore_random_parameters():
    a, b = build("chain", 5, 5, 99, 100, 123), build("chain", 30, 30, 10, 0, 1)
    assert a.vehicles == b.vehicles and a.n == 7
    assert build("steal", 1, 1, 1, 1, 1).n == 2 and build("p4", 1, 1, 1, 1, 1).n == 2 and build("paths", 1, 1, 1, 1, 1).n == 6


def test_classify_and_cost_gap():
    opt = Matching(((0, 0),), 10)
    assert ev.classify(type("R", (), {"count": 1, "cost": 10})(), opt) == ev.OPTIMAL
    assert ev.classify(type("R", (), {"count": 1, "cost": 12})(), opt) == ev.MISMATCH
    assert ev.classify(type("R", (), {"count": 0, "cost": 0})(), Matching((), 0)) == ev.NONE
    assert ev.cost_gap_pct(18, 10) == pytest.approx(80.0) and ev.cost_gap_pct(5, 0) is None


@pytest.mark.parametrize("net,count,cost,marginal,greedy_cost,ap_gap", [
    ("steal", 2, 10, [4, 6], 18, 80.0),
    ("p4", 2, 20, [2, 18], None, 0.0),
    ("chain", 7, 70, [2, 2, 2, 2, 2, 2, 58], None, 0.0),
])
def test_verdict_of_the_fixed_nets(net, count, cost, marginal, greedy_cost, ap_gap):
    level, code, d = ev.verdict(ev.analyse(build(net, 20, 20, 40, 0, 2)))
    assert (level, code) == ("success", ev.OPTIMAL)
    assert (d["count"], d["cost"], d["marginal"], d["ap_edge_gap_pct"]) == (count, cost, marginal, pytest.approx(ap_gap))
    assert d["cert"]["all_ok"] and d["last_w"] == marginal[-1] and d["p"] == marginal[-1]
    if greedy_cost is not None:
        assert d["greedy_cost"] == greedy_cost and d["greedy_gap_pct"] == pytest.approx(80.0)
    else:
        assert d["greedy_gap_pct"] is None            # weniger Paare: Kosten nicht vergleichbar


def test_verdict_none_without_any_feasible_edge():
    sc = next(s for s in (generate(3, 3, 10, 0, k) for k in range(200)) if not s.feasible.any())
    level, code, d = ev.verdict(ev.analyse(sc))
    assert (level, code) == ("info", ev.NONE) and d["count"] == 0 and d["last_w"] is None and d["mean_w"] is None


def test_compare_table_rows():
    rows = ev.compare_table(ev.analyse(generate(20, 20, 40, 0, 165)))
    assert [r["label"] for r in rows][-1] == "Ungarische Methode" and len(rows) == 5
    assert rows[-1]["cost_gap_pct"] == 0.0 and rows[0]["cost_gap_pct"] is None      # Greedy hat hier weniger Paare
    assert rows[2]["cost_gap_pct"] > 0 and rows[3]["cost_gap_pct"] > rows[2]["cost_gap_pct"]


def test_distribution_fields_and_shares():
    d = ev.distribution(20, 20, 40, 0)
    assert d["n_seeds"] == 100 == d["n_valid"] and d["share_optimal"] == 1.0
    assert set(d["gaps"]) == {"Verbesserungswege ab Greedy", "Verbesserungswege ab leer", "Verbesserungswege ab Greedy, Tiefensuche"}
    assert all(len(v) == 100 for v in d["gaps"].values()) and all(g >= 0 for v in d["gaps"].values() for g in v)
    assert d["scanned_mean"] > d["ap_edge_scanned_mean"] and d["p_median"] > 0 and d["last_ratio_median"] > 1


def test_distribution_is_repeatable():
    assert ev.distribution(15, 15, 40, 25) == ev.distribution(15, 15, 40, 25)


def test_distribution_without_feasible_pairs():
    bad = tuple(s for s in range(60) if not generate(3, 3, 10, 0, s).feasible.any())
    assert len(bad) >= 3
    assert ev.distribution(3, 3, 10, 0, seeds=bad)["n_valid"] == 0 and ev.effort_table(3, 3, 10, 0, seeds=bad) == []


def test_effort_table_rows():
    rows = ev.effort_table(20, 20, 40, 0)
    assert [r["label"] for r in rows][-1] == "Ungarische Methode" and len(rows) == 5
    assert rows[-1]["pairs_max"] == 1.0 and rows[-1]["gap_median"] == 0.0 and rows[0]["rounds"] is None


def test_reach_sweep_rows():
    rows = ev.reach_sweep(15, 15, 0, values=(10, 40, 150), seeds=C.SWEEP_SEEDS[:10])
    assert [r["x"] for r in rows] == [10, 40, 150] and all(r["scanned"] > 0 for r in rows) and rows[-1]["ap_scanned"] == 0.0


def test_scaling_rows_and_reach_rule():
    rows = ev.scaling(ns=(10, 20), seeds=C.SCALE_SEEDS[:3])
    assert [r["n"] for r in rows] == [10, 20] and [r["reach"] for r in rows] == [57, 40] and all(r["scanned"] > r["ap_scanned"] for r in rows)


def test_cell_rows_are_integers():
    rows = ev.cell_rows(10, 10, 40, 0, tuple(C.SWEEP_SEEDS[:5]))
    for row in rows:
        for key, val in row.items():
            assert all(isinstance(v, int) for v in (val if isinstance(val, tuple) else (val,))), key
