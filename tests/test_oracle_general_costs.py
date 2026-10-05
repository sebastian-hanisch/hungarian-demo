"""Unabhängiges Orakel auf zufälligen Kostenmatrizen (nicht geometrisch, viele Nullen und Gleichstände, rechteckig, unvollständig): lexikografisches Optimum
(größte Paarzahl, dann geringste Kosten) per Brute Force über alle Paarmengen und per scipy `linear_sum_assignment`; Grenzkosten = billigste
Paarungen mit genau k Paaren (Brute Force); Dualzulässigkeit der Preise nach eigener Prüfung. Kosten müssen >= 0 sein (Potenziale starten bei 0)."""

import random
from types import SimpleNamespace

import numpy as np
import pytest

from hu_algorithm import hungarian


def _brute(n, m, feas, cost):
    best = {}

    def rec(i, used, k, c):
        if i == n:
            if k not in best or c < best[k]:
                best[k] = c
            return
        rec(i + 1, used, k, c)
        for j in range(m):
            if j not in used and feas[i][j]:
                rec(i + 1, used | {j}, k + 1, c + cost[i][j])

    rec(0, frozenset(), 0, 0)
    return best


def test_hungarian_on_random_cost_matrices_against_brute_force_and_scipy():
    optimize = pytest.importorskip("scipy.optimize")
    rng = random.Random(20261004)
    for t in range(250):
        n, m = rng.randint(1, 6), rng.randint(1, 6)
        p, hi = rng.choice([0.2, 0.5, 0.8, 1.0]), rng.choice([0, 1, 2, 3, 10, 100])
        feas = [[rng.random() < p for _ in range(m)] for _ in range(n)]
        cost = [[rng.randint(0, hi) for _ in range(m)] for _ in range(n)]
        sc = SimpleNamespace(n=n, m=m, feasible=np.array(feas, dtype=bool).reshape(n, m), cost=np.array(cost, dtype=np.int64).reshape(n, m))
        res = hungarian(sc)
        best = _brute(n, m, feas, cost)
        top = max(best)
        assert (res.count, res.cost) == (top, best[top])
        if sc.feasible.any():
            big = int(sc.cost.max()) * min(n, m) + 1
            r, c = optimize.linear_sum_assignment(np.where(sc.feasible, sc.cost, big))
            real = [(i, j) for i, j in zip(r, c) if sc.feasible[i, j]]
            assert (len(real), int(sum(sc.cost[i, j] for i, j in real))) == (res.count, res.cost)
        running = [0]
        for w in res.marginal:
            running.append(running[-1] + w)
        assert running == [best[k] for k in range(len(running))] and len(running) == top + 1       # Grenzkosten: billigste k-Paarung
        assert list(res.marginal) == sorted(res.marginal)
        for i in range(n):
            for j in range(m):
                if feas[i][j]:
                    assert res.pi_o[j] - res.pi_v[i] <= cost[i][j]                                   # Dualzulässigkeit
        assert all(res.pi_o[j] - res.pi_v[i] == cost[i][j] for i, j in res.pairs)                   # gewählte Kanten straff
