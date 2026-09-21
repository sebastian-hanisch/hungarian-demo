"""Auswertung: eine Karte (`analyse`, `verdict`, `compare_table`), viele Karten (`distribution`, `effort_table`), Reichweite-Sweep und Aufwand-Experiment.

Alle Größen kommen aus ganzen Zahlen und deterministischen Verfahren; nur die Anzeige-Statistiken (Anteile, Mediane) sind Gleitkomma.
Aufwand wird in durchsuchten Kanten gezählt (Fahrzeug->Auftrag-Relaxierungen, vergleichbar mit der Verbesserungswege-Demo), nie in Sekunden.
"""

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

import hu_constants as C
from hu_algorithm import certificate, hungarian
from hu_augment import augment, start_pairs
from hu_greedy import RULES, optimum, run_rule
from hu_scenario import build, generate

OPTIMAL, MISMATCH, NONE = "optimal", "mismatch", "none"


@dataclass
class Analysis:
    scenario: object
    result: object       # hu_algorithm.Result (Ungarische Methode)
    opt: object          # Referenz aus Stück 1 (Messlatte), nur als Gegenprobe
    greedy: dict         # {"edge": Matching, "order": Matching}
    ap_edge: object      # Verbesserungswege vom Greedy-Start (Stück 2)
    ap_empty: object     # Verbesserungswege vom leeren Start (Stück 2)


def analyse(sc):
    ge = run_rule(sc, "edge")
    return Analysis(sc, hungarian(sc), optimum(sc), {r: run_rule(sc, r) for r in RULES}, augment(sc, ge.pairs, "bfs"), augment(sc, (), "bfs"))


def cost_gap_pct(cost, opt_cost):
    """Mehrkosten in Prozent des Optimums bei gleicher Paarzahl; nur definiert, wenn das Optimum positive Kosten hat."""
    return None if opt_cost <= 0 else 100.0 * (cost - opt_cost) / opt_cost


def classify(res, opt):
    if opt.count == 0:
        return NONE
    return OPTIMAL if (res.count, res.cost) == (opt.count, opt.cost) else MISMATCH


def verdict(a):
    """(Stufe, Code, Zahlen) für die Anzeige; `Zahlen` enthält jede Zahl, die der Text nennt."""
    r, o = a.result, a.opt
    code = classify(r, o)
    marg = list(r.marginal)
    cert = certificate(a.scenario, r)
    data = {"count": r.count, "opt_count": o.count, "cost": r.cost, "opt_cost": o.cost, "rounds": len(r.rounds), "marginal": marg, "last_w": marg[-1] if marg else None,
            "mean_w": sum(marg) / len(marg) if marg else None, "p": r.p, "scanned": r.scanned_total, "pops": r.pops_total, "pushes": r.pushes_total, "matched_arcs": r.matched_arcs_total,
            "greedy_count": a.greedy["edge"].count, "greedy_cost": a.greedy["edge"].cost, "greedy_gap_pct": cost_gap_pct(a.greedy["edge"].cost, o.cost) if a.greedy["edge"].count == o.count else None,
            "ap_edge_cost": a.ap_edge.cost, "ap_edge_gap_pct": cost_gap_pct(a.ap_edge.cost, o.cost), "ap_edge_rounds": len(a.ap_edge.rounds), "ap_edge_scanned": a.ap_edge.scanned_total,
            "ap_empty_cost": a.ap_empty.cost, "ap_empty_gap_pct": cost_gap_pct(a.ap_empty.cost, o.cost), "ap_empty_scanned": a.ap_empty.scanned_total,
            "cert": cert, "edges": int(a.scenario.feasible.sum())}
    level = {NONE: "info", OPTIMAL: "success", MISMATCH: "error"}[code]
    return level, code, data


def compare_table(a):
    """Zeilen für Greedy, Verbesserungswege und Ungarische Methode auf der aktuellen Karte."""
    o = a.opt
    rows = []
    for label, count, cost, rounds, scanned in (
        ("Greedy: billigste Kante zuerst", a.greedy["edge"].count, a.greedy["edge"].cost, None, None),
        ("Greedy: Auftrag für Auftrag", a.greedy["order"].count, a.greedy["order"].cost, None, None),
        ("Verbesserungswege ab Greedy", a.ap_edge.count, a.ap_edge.cost, len(a.ap_edge.rounds), a.ap_edge.scanned_total),
        ("Verbesserungswege ab leer", a.ap_empty.count, a.ap_empty.cost, len(a.ap_empty.rounds), a.ap_empty.scanned_total),
        ("Ungarische Methode", a.result.count, a.result.cost, len(a.result.rounds), a.result.scanned_total),
    ):
        rows.append({"label": label, "count": count, "cost": cost, "rounds": rounds, "scanned": scanned,
                     "cost_gap_pct": cost_gap_pct(cost, o.cost) if count == o.count else None})
    return rows


# --- viele Karten --------------------------------------------------------------------------------------------------------------

@lru_cache(maxsize=256)
def cell_rows(n, m, reach, ballung, seeds):
    """Je Seed: Optimum, Ungarische Methode und die Vergleichsverfahren als Ganzzahlen (plattformunabhängig). Rückgabe: Tupel von Dicts."""
    rows = []
    for s in seeds:
        sc = generate(n, m, reach, ballung, s)
        o = optimum(sc)
        h = hungarian(sc, record=False)
        ge, go = run_rule(sc, "edge"), run_rule(sc, "order")
        ae, a0, ad = augment(sc, ge.pairs, "bfs", record=False), augment(sc, (), "bfs", record=False), augment(sc, ge.pairs, "dfs", record=False)
        marg = h.marginal
        rows.append({"opt": (o.count, o.cost), "edges": int(sc.feasible.sum()), "hung": (h.count, h.cost), "rounds": len(h.rounds), "scanned": h.scanned_total, "pops": h.pops_total,
                     "pushes": h.pushes_total, "matched_arcs": h.matched_arcs_total, "p": h.p, "last_w": marg[-1] if marg else 0, "sum_w": sum(marg),
                     "greedy_edge": (ge.count, ge.cost), "greedy_order": (go.count, go.cost), "ap_edge": (ae.count, ae.cost, len(ae.rounds), ae.scanned_total),
                     "ap_empty": (a0.count, a0.cost, len(a0.rounds), a0.scanned_total), "ap_dfs": (ad.count, ad.cost, len(ad.rounds), ad.scanned_total)})
    return tuple(rows)


def distribution(n, m, reach, ballung, seeds=C.DIST_SEEDS):
    """Verteilung über viele Karten: Optimalität der Ungarischen Methode, Aufwand, Grenzkosten und die Kostenlücken der Vergleichsverfahren."""
    rows = [r for r in cell_rows(n, m, reach, ballung, tuple(seeds)) if r["opt"][0] > 0]
    nv = len(rows)
    if nv == 0:
        return {"n_seeds": len(seeds), "n_valid": 0}
    gap = lambda key: [100.0 * (r[key][1] - r["opt"][1]) / r["opt"][1] for r in rows if r["opt"][1] > 0 and r[key][0] == r["opt"][0]]
    ratios = [r["last_w"] / (r["sum_w"] / r["hung"][0]) for r in rows if r["sum_w"] > 0]
    mean = lambda key: float(np.mean([r[key] for r in rows]))
    return {
        "n_seeds": len(seeds), "n_valid": nv, "share_optimal": float(np.mean([r["hung"] == r["opt"] for r in rows])),
        "rounds_mean": mean("rounds"), "scanned_mean": mean("scanned"), "pops_mean": mean("pops"), "pushes_mean": mean("pushes"), "matched_arcs_mean": mean("matched_arcs"),
        "edges_mean": mean("edges"), "p_mean": mean("p"), "p_median": float(np.median([r["p"] for r in rows])), "last_ratio_median": float(np.median(ratios)) if ratios else None,
        "ap_edge_scanned_mean": float(np.mean([r["ap_edge"][3] for r in rows])), "ap_empty_scanned_mean": float(np.mean([r["ap_empty"][3] for r in rows])),
        "ap_dfs_scanned_mean": float(np.mean([r["ap_dfs"][3] for r in rows])), "opt_pairs_mean": float(np.mean([r["opt"][0] for r in rows])),
        "gaps": {"Verbesserungswege ab Greedy": gap("ap_edge"), "Verbesserungswege ab leer": gap("ap_empty"), "Verbesserungswege ab Greedy, Tiefensuche": gap("ap_dfs")},
        "greedy_gaps": gap("greedy_edge"), "greedy_pairs_mean": float(np.mean([r["greedy_edge"][0] for r in rows])),
        "share_greedy_max": float(np.mean([r["greedy_edge"][0] == r["opt"][0] for r in rows])),
    }


def _median(values):
    return float(np.median(values)) if len(values) else None


def effort_table(n, m, reach, ballung, seeds=C.DIST_SEEDS):
    """Zeilen für Greedy, Verbesserungswege (Stück 2) und Ungarische Methode: Runden, durchsuchte Kanten, Mehrkosten (Median) über die festen Karten."""
    rows = [r for r in cell_rows(n, m, reach, ballung, tuple(seeds)) if r["opt"][0] > 0]
    if not rows:
        return []
    def line(label, key, cnt, rnd=None, scn=None):
        gaps = [100.0 * (r[key][1] - r["opt"][1]) / r["opt"][1] for r in rows if r["opt"][1] > 0 and r[key][0] == r["opt"][0]]
        return {"label": label, "pairs_max": float(np.mean([r[key][0] == r["opt"][0] for r in rows])), "gap_median": _median(gaps),
                "rounds": None if rnd is None else float(np.mean([r[key][rnd] for r in rows])), "scanned": None if scn is None else float(np.mean([r[key][scn] for r in rows]))}
    out = [line("Greedy: billigste Kante zuerst", "greedy_edge", 0), line("Verbesserungswege ab Greedy", "ap_edge", 0, 2, 3), line("Verbesserungswege ab leer", "ap_empty", 0, 2, 3),
           line("Verbesserungswege ab Greedy, Tiefensuche", "ap_dfs", 0, 2, 3)]
    out.append({"label": "Ungarische Methode", "pairs_max": float(np.mean([r["hung"][0] == r["opt"][0] for r in rows])),
                "gap_median": _median([100.0 * (r["hung"][1] - r["opt"][1]) / r["opt"][1] for r in rows if r["opt"][1] > 0]),
                "rounds": float(np.mean([r["rounds"] for r in rows])), "scanned": float(np.mean([r["scanned"] for r in rows]))})
    return out


def reach_sweep(n, m, ballung, values=C.REACH_SWEEP, seeds=C.SWEEP_SEEDS):
    """Je Reichweite: durchsuchte Kanten der Ungarischen Methode und der Verbesserungswege ab Greedy, Preisdecke P und mediane Mehrkosten der Verbesserungswege."""
    out = []
    for reach in values:
        d = distribution(n, m, reach, ballung, seeds)
        if d["n_valid"] == 0:
            out.append({"x": reach, "scanned": None, "ap_scanned": None, "p": None, "ap_gap": None})
            continue
        out.append({"x": reach, "scanned": d["scanned_mean"], "ap_scanned": d["ap_edge_scanned_mean"], "p": d["p_mean"], "ap_gap": _median(d["gaps"]["Verbesserungswege ab Greedy"])})
    return out


def scaling(ns=C.SCALE_NS, seeds=C.SCALE_SEEDS):
    """Aufwand wächst mit der Karte: n = m bei konstantem mittleren Grad (Reichweite ~ 1/sqrt(n)); durchsuchte Kanten der Ungarischen Methode gegen Verbesserungswege ab Greedy."""
    out = []
    for n in ns:
        reach = max(5, round(C.SCALE_REACH_AT_20 * math.sqrt(20 / n)))
        acc = []
        for s in seeds:
            sc = generate(n, n, reach, 0, s)
            h = hungarian(sc, record=False)
            a = augment(sc, run_rule(sc, "edge").pairs, "bfs", record=False)
            acc.append((int(sc.feasible.sum()), len(h.rounds), h.scanned_total, h.pops_total, a.scanned_total))
        arr = np.array(acc, dtype=float).mean(axis=0)
        out.append({"n": n, "reach": reach, "edges": float(arr[0]), "rounds": float(arr[1]), "scanned": float(arr[2]), "pops": float(arr[3]), "ap_scanned": float(arr[4])})
    return out


def scenario_from_settings(net, n, m, reach, ballung, seed):
    return build(net, n, m, reach, ballung, seed)
