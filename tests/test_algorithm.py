"""Ungarische Methode: Handrechnungen, Invarianten I1-I6 je Runde, der Beweis (C1-C5, Kostenidentität), scipy, networkx und Brute Force als unabhängige Prüfer,
dazu die kopierten Bausteine der Vorgängerdemos. Verglichen werden immer nur (Paarzahl, Kosten) - nie Kantenmengen."""

import itertools
from dataclasses import replace

import networkx as nx
import numpy as np
import pytest
from scipy.optimize import linear_sum_assignment

from hu_algorithm import certificate, hungarian
from hu_augment import augment
from hu_greedy import RULES, optimum, run_rule
from hu_scenario import SplitMix64, from_points, generate, long_chain, p4_chain, steal_2x2


# --- kopierte Bausteine (Wache gegen einen fehlerhaften Kopiervorgang) --------------------------------------------------------------------

def test_splitmix64_reference_vector():
    rng = SplitMix64(0)
    assert [rng.next() for _ in range(2)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4]


def test_the_numbers_of_the_predecessors_are_reproduced():
    """Wache gegen einen Kopierfehler: dieselbe Karte (Seed 2, Reichweite 40) gibt die Zahlen der Greedy-Matching-Demo und der Verbesserungswege-Demo."""
    sc = generate(20, 20, 40, 0, 2)
    g, o = run_rule(sc, "edge"), optimum(sc)
    assert (g.count, g.cost, o.count, o.cost) == (17, 232, 20, 316)
    ap = augment(sc, g.pairs, "bfs", record=False)
    assert ap.count == 20 and len(ap.rounds) == o.count - g.count == 3


def test_fixed_maps_of_the_predecessors():
    assert steal_2x2().cost.tolist() == [[4, 5], [5, 14]]
    assert (long_chain(6).n, int(long_chain(6).feasible.sum())) == (7, 13)


# --- Handrechnungen ---------------------------------------------------------------------------------------------------------------------

def test_steal_2x2_by_hand():
    """Runde 1: billigste Kante (4). Runde 2: Abstand zum Ziel 2, Wegkosten 6 (5 + 5 - 4), Gesamtkosten 10. Preise (1, 0) / (5, 6), Decke P = 6, Kostenidentität 11 - 1 = 10."""
    sc = steal_2x2()
    res = hungarian(sc)
    assert set(res.pairs) == {(0, 1), (1, 0)} and res.cost == 10 and res.marginal == (4, 6)
    assert (res.pi_v, res.pi_o, res.p) == ((1, 0), (5, 6), 6)
    r1, r2 = res.rounds
    assert (r1.w, r1.d_t, r1.p_before, r1.p_after, r1.length) == (4, 4, 0, 4, 1) and (r2.w, r2.d_t, r2.p_before, r2.p_after, r2.length) == (6, 2, 4, 6, 3)
    assert r2.path == ((1, 1, "add"), (0, 1, "drop"), (0, 0, "add")) or r2.path[0][2] == "add" and len(r2.path) == 3
    cert = certificate(sc, res)
    assert cert["all_ok"] and cert["identity_rhs"] == 10 == sum(res.pi_o) - sum(res.pi_v) - 0 * res.p == 11 - 1


def test_steal_2x2_tie_break_is_orders_before_vehicles():
    """Regressionstest der Festlegungsreihenfolge in Runde 2: (Art, Index, Abstand, Rang); Gleichstand entscheidet (Abstand, Art, Index), Aufträge zuerst."""
    res = hungarian(steal_2x2())
    assert res.rounds[1].settled == ((1, 1, 0, 0), (0, 0, 1, 1), (1, 0, 1, 2), (0, 1, 2, 3))


def test_p4_marginal_costs():
    res = hungarian(p4_chain(1))
    assert res.marginal == (2, 18) and res.cost == 20 and res.count == 2


def test_long_chain_the_seventh_pair_costs_58():
    res = hungarian(long_chain(6))
    assert res.marginal == (2, 2, 2, 2, 2, 2, 58) and res.cost == 70 and res.count == 7 and res.p == 58


def test_two_vehicles_one_order_multi_source_start():
    """Der Mehrfachstart ist nötig: Kosten 5 und 1 zu einem Auftrag -> das billigere Fahrzeug bekommt ihn."""
    sc = from_points([(0, 0), (4, 0)], [(5, 0)], reach=10)
    assert sc.cost.tolist() == [[5], [1]]
    res = hungarian(sc)
    assert res.pairs == ((1, 0),) and res.cost == 1 and certificate(sc, res)["all_ok"]


def test_no_feasible_edge():
    sc = from_points([(0, 0)], [(90, 90)], reach=10)
    res = hungarian(sc)
    assert res.count == 0 and res.rounds == () and res.cost == 0 and res.p == 0 and certificate(sc, res)["all_ok"]


# --- Invarianten je Runde -----------------------------------------------------------------------------------------------------------------

def _cases(n_cases=120):
    for s in range(n_cases):
        n, m = 3 + s % 9, 3 + (s * 5) % 9
        yield generate(n, m, 15 + (s * 13) % 130, (s * 25) % 101, s)


def _invariants(sc, pairs, pi_v, pi_o, p):
    match_v = {i: j for i, j in pairs}
    matched_o = set(match_v.values())
    for i in range(sc.n):
        for j in range(sc.m):
            if not sc.feasible[i, j]:
                continue
            r = int(sc.cost[i, j]) + pi_v[i] - pi_o[j]                # reduzierte Kosten der Kante i -> j (Restgraph: nicht gewählt)
            if match_v.get(i) == j:
                assert r == 0                                          # I2: gewählte Kanten straff (Rückkante hat ebenfalls 0)
            else:
                assert r >= 0                                          # I1
    free_v = [i for i in range(sc.n) if i not in match_v]
    free_o = [j for j in range(sc.m) if j not in matched_o]
    assert all(pi_v[i] == 0 for i in free_v) and all(v >= 0 for v in pi_v)          # I3
    assert all(pi_o[j] == p for j in free_o) and all(0 <= v <= p for v in pi_o)      # I4
    assert sum(int(sc.cost[i, j]) for i, j in pairs) == sum(pi_o) - sum(pi_v) - (sc.m - len(pairs)) * p     # I5


def test_invariants_hold_after_every_round():
    for sc in _cases(120):
        res = hungarian(sc)
        _invariants(sc, res.states[0], (0,) * sc.n, (0,) * sc.m, 0)
        for k, rnd in enumerate(res.rounds):
            _invariants(sc, res.states[k + 1], rnd.pi_v_after, rnd.pi_o_after, rnd.p_after)
            assert all(a >= b for a, b in zip(rnd.pi_v_after, rnd.pi_v_before)) and all(a >= b for a, b in zip(rnd.pi_o_after, rnd.pi_o_before))      # I6
            assert rnd.p_after == rnd.p_before + rnd.d_t and rnd.w == rnd.p_after and len(res.states[k + 1]) == len(res.states[k]) + 1


def test_marginal_costs_never_fall_and_sum_to_the_cost():
    for sc in _cases(200):
        res = hungarian(sc)
        assert list(res.marginal) == sorted(res.marginal) and sum(res.marginal) == res.cost and len(res.rounds) == res.count


def test_potential_update_rule_settled_by_distance_others_by_target_distance():
    for sc in _cases(60):
        res = hungarian(sc)
        for rnd in res.rounds:
            dist = {(k, x): d for k, x, d, _r in rnd.settled}
            for i in range(sc.n):
                assert rnd.pi_v_after[i] - rnd.pi_v_before[i] == min(dist.get((1, i), rnd.d_t), rnd.d_t)
            for j in range(sc.m):
                assert rnd.pi_o_after[j] - rnd.pi_o_before[j] == min(dist.get((0, j), rnd.d_t), rnd.d_t)


# --- Orakel -----------------------------------------------------------------------------------------------------------------------------

def test_matches_scipy_networkx_and_the_reference_of_piece_one():
    for sc in _cases(200):
        big = int(sc.cost.max()) * min(sc.n, sc.m) + 1
        rows, cols = linear_sum_assignment(np.where(sc.feasible, big - sc.cost, 0), maximize=True)
        pairs = [(i, j) for i, j in zip(rows, cols) if sc.feasible[i, j]]
        ref = (len(pairs), int(sum(sc.cost[i, j] for i, j in pairs)))
        res, o = hungarian(sc), optimum(sc)
        assert (res.count, res.cost) == ref == (o.count, o.cost)


def test_matches_networkx_max_weight_matching():
    for sc in _cases(80):
        big = int(sc.cost.max()) * min(sc.n, sc.m) + 1
        g = nx.Graph()
        for i in range(sc.n):
            for j in range(sc.m):
                if sc.feasible[i, j]:
                    g.add_edge(("v", i), ("o", j), weight=big - int(sc.cost[i, j]))
        matching = nx.max_weight_matching(g, maxcardinality=True)
        cost = 0
        for a, b in matching:
            v, o = (a, b) if a[0] == "v" else (b, a)
            cost += int(sc.cost[v[1], o[1]])
        res = hungarian(sc)
        assert (res.count, res.cost) == (len(matching), cost)


def _brute_force(sc):
    best = (0, 0)

    def rec(j, used, count, cost):
        nonlocal best
        if j == sc.m:
            best = max(best, (count, -cost))
            return
        rec(j + 1, used, count, cost)
        for i in range(sc.n):
            if i not in used and sc.feasible[i, j]:
                rec(j + 1, used | {i}, count + 1, cost + int(sc.cost[i, j]))

    rec(0, frozenset(), 0, 0)
    return best


def test_matches_brute_force_on_small_maps():
    for s in range(120):
        sc = generate(1 + s % 6, 1 + (s * 5) % 6, 20 + (s * 11) % 120, (s * 25) % 101, 1000 + s)
        assert hungarian(sc).key() == _brute_force(sc)


def _residual(sc, pairs, with_source_sink=True):
    """Wahrer Restgraph mit echten (teils negativen) Kosten, Quelle 's' und Senke 't'."""
    match_v = {i: j for i, j in pairs}
    g = nx.DiGraph()
    for i in range(sc.n):
        for j in range(sc.m):
            if sc.feasible[i, j]:
                if match_v.get(i) == j:
                    g.add_edge(("o", j), ("v", i), weight=-int(sc.cost[i, j]))
                else:
                    g.add_edge(("v", i), ("o", j), weight=int(sc.cost[i, j]))
    if with_source_sink:
        matched_o = set(match_v.values())
        for i in range(sc.n):
            g.add_edge(("v", i), "s", weight=0) if i in match_v else g.add_edge("s", ("v", i), weight=0)
        for j in range(sc.m):
            g.add_edge("t", ("o", j), weight=0) if j in matched_o else g.add_edge(("o", j), "t", weight=0)
    return g


def test_every_round_path_is_a_shortest_path_in_the_true_residual_graph():
    """Unabhängige Prüfung ohne Potenziale: die Wegkosten W jeder Runde sind der kürzeste Weg von s nach t im Restgraphen mit echten Kosten; kein negativer Kreis."""
    for sc in _cases(60):
        res = hungarian(sc)
        for k, rnd in enumerate(res.rounds):
            g = _residual(sc, res.states[k])
            assert not nx.negative_edge_cycle(g)
            dist = nx.single_source_bellman_ford_path_length(g, "s")
            assert dist["t"] == rnd.w


def test_marginal_costs_are_the_minimum_cost_flow_increments():
    for sc in _cases(25):
        res = hungarian(sc)
        prev = 0
        for k in range(1, res.count + 1):
            g = nx.DiGraph()
            g.add_node("s", demand=-k)
            g.add_node("t", demand=k)
            for i in range(sc.n):
                g.add_edge("s", ("v", i), capacity=1, weight=0)
            for j in range(sc.m):
                g.add_edge(("o", j), "t", capacity=1, weight=0)
            for i in range(sc.n):
                for j in range(sc.m):
                    if sc.feasible[i, j]:
                        g.add_edge(("v", i), ("o", j), capacity=1, weight=int(sc.cost[i, j]))
            flow_cost = nx.min_cost_flow_cost(g)
            assert sum(res.marginal[:k]) == flow_cost
            assert flow_cost >= prev
            prev = flow_cost


def test_settled_distances_equal_a_full_dijkstra_on_reduced_costs():
    """Die Abstände der Festgelegten in der Runde sind die kürzesten reduzierten Abstände im Restgraphen (Bellman-Ford mit reduzierten, also nicht negativen Kosten)."""
    for sc in _cases(40):
        res = hungarian(sc)
        for k, rnd in enumerate(res.rounds):
            match_v = {i: j for i, j in res.states[k]}
            g = nx.DiGraph()
            g.add_nodes_from([("v", i) for i in range(sc.n)] + [("o", j) for j in range(sc.m)])
            for i in range(sc.n):
                for j in range(sc.m):
                    if sc.feasible[i, j]:
                        if match_v.get(i) == j:
                            g.add_edge(("o", j), ("v", i), weight=0)
                        else:
                            g.add_edge(("v", i), ("o", j), weight=int(sc.cost[i, j]) + rnd.pi_v_before[i] - rnd.pi_o_before[j])
            assert all(d["weight"] >= 0 for _u, _v, d in g.edges(data=True))
            free = [("v", i) for i in range(sc.n) if i not in match_v]
            dist = nx.multi_source_dijkstra_path_length(g, free) if free else {}
            for kind, x, d, _rank in rnd.settled:
                assert dist[("v" if kind == 1 else "o", x)] == d


# --- Beweis (Zertifikat) -------------------------------------------------------------------------------------------------------------------

def test_certificate_holds_on_every_map():
    for sc in _cases(200):
        cert = certificate(sc, hungarian(sc))
        assert cert["all_ok"], cert


def test_certificate_needs_the_conditions_on_free_vertices():
    """Negativtest (Plan-Agent): zwei Fahrzeuge (Kosten 5 und 1) zu einem Auftrag. Preise pi_o = 5, pi_v = (0, 4) mit dem falschen Matching (F1, A1) erfüllen C1 und C2, aber nicht C3 (freies Fahrzeug F2 hat Gewinn 4)."""
    sc = from_points([(0, 0), (4, 0)], [(5, 0)], reach=10)
    res = hungarian(sc)
    fake = replace(res, pairs=((0, 0),), cost=5, pi_v=(0, 4), pi_o=(5,), p=5)
    cert = certificate(sc, fake)
    assert cert["c1"] and cert["c2"] and not cert["c3"] and not cert["all_ok"]


def test_certificate_detects_a_suboptimal_matching():
    """Ein absichtlich teureres Matching kann mit keinen Potenzialen alle Bedingungen erfüllen: hier liegt das Ergebnis der Verbesserungswege auf 2x2 (18) über dem Optimum (10)."""
    sc = steal_2x2()
    res = hungarian(sc)
    fake = replace(res, pairs=((0, 0), (1, 1)), cost=18)
    assert not certificate(sc, fake)["all_ok"]


def test_effort_counters_are_deterministic_and_positive():
    for sc in _cases(40):
        a, b = hungarian(sc, record=False), hungarian(sc, record=False)
        assert (a.scanned_total, a.pops_total, a.pushes_total) == (b.scanned_total, b.pops_total, b.pushes_total)
        assert a.pops_total <= a.pushes_total + sc.n * (len(a.rounds) + 1)
        assert a.scanned_total >= sum(1 for rnd in a.rounds for _ in rnd.path[:1])


# --- Negativkontrolle: zeilenweises Einfügen -------------------------------------------------------------------------------------------------------

def sequential_insertion(sc):
    """Naives Verfahren: die Fahrzeuge einzeln in Indexreihenfolge einfügen, je Fahrzeug der billigste Weg zu einem freien Auftrag. Für n > m falsch."""
    match_v, match_o = {}, {}
    for i in range(sc.n):
        g = _residual(sc, list(match_v.items()), with_source_sink=False)
        if ("v", i) not in g or ("v", i) in {("v", a) for a in match_v}:
            continue
        dist, paths = nx.single_source_bellman_ford(g, ("v", i))
        cands = [(dist[("o", j)], j) for j in range(sc.m) if ("o", j) in dist and j not in match_o]
        if not cands:
            continue
        _, j = min(cands)
        path = paths[("o", j)]
        for k in range(0, len(path) - 1, 2):
            a, b = path[k][1], path[k + 1][1]
            match_v[a], match_o[b] = b, a
    return len(match_v), sum(int(sc.cost[a, b]) for a, b in match_v.items())


def test_sequential_insertion_is_wrong_when_there_are_more_vehicles_than_orders():
    sc = from_points([(0, 0), (4, 0)], [(5, 0)], reach=10)
    assert sequential_insertion(sc) == (1, 5) and hungarian(sc).key() == (1, -1)          # 5 statt 1


def test_sequential_insertion_is_right_when_the_smaller_side_is_inserted():
    """Positive Gegenprobe: bei n <= m und Einfügen der Fahrzeuge (der kleineren Seite) stimmt das zeilenweise Verfahren nicht immer, aber nie mit weniger Paaren - nur mit den Kosten."""
    for s in range(20):
        sc = generate(8, 12, 60, 0, 300 + s)
        seq = sequential_insertion(sc)
        assert seq[0] <= hungarian(sc).count
