"""Presets: vollständig, in den Grenzen, und jede Beispielkarte zeigt, was ihr Hilfetext behauptet."""

import numpy as np
import pytest

import hu_constants as C
import hu_evaluation as ev
import hu_presets as P
from hu_scenario import build

KEYS = set(P.PRESET_KEYS)


def _sc(p):
    return build(p["net"], p["n"], p["m"], p["reach"], p["ballung"], p["seed"])


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP) and len(C.PRESETS) == 8
    assert all(C.PRESET_HELP[name].strip() for name in C.PRESETS)
    for name, p in C.PRESETS.items():
        assert set(p) == KEYS, name


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_preset_values_are_inside_the_bounds_and_on_the_step_grid(name):
    p = C.PRESETS[name]
    assert p["net"] in C.NETS and p["view"] in C.VIEW_LABELS
    for key, state_key in P.PRESET_KEYS.items():
        spec = P.SETTING_SPECS[state_key]
        if spec.lo is not None:
            assert spec.lo <= p[key] <= spec.hi, (name, key)
    assert (p["reach"] - C.REACH_MIN) % 5 == 0 and p["ballung"] % 25 == 0


def test_setting_specs_have_room_to_move():
    """Ein Regler mit lo == hi würde Streamlit abstürzen lassen."""
    assert all(spec.lo < spec.hi for spec in P.SETTING_SPECS.values() if spec.lo is not None)


def test_presets_use_seeds_outside_the_distribution_set():
    for name, p in C.PRESETS.items():
        assert p["seed"] not in C.DIST_SEEDS, name


def test_the_mid_reach_map_is_the_map_of_the_previous_piece_and_the_two_views_share_it():
    mid, paths = C.PRESETS["🗺️ Mittlere Reichweite"], C.PRESETS["🛣️ Kürzeste-Wege-Sicht"]
    assert (mid["n"], mid["m"], mid["reach"], mid["ballung"], mid["seed"]) == (20, 20, 40, 0, 165) == (C.DEFAULT_N, C.DEFAULT_M, C.DEFAULT_REACH, C.DEFAULT_BALLUNG, C.DEFAULT_SEED)
    assert all(paths[k] == mid[k] for k in ("net", "n", "m", "reach", "ballung", "seed")) and (mid["view"], paths["view"]) == ("prices", "paths")


def test_every_preset_is_optimal_and_certified():
    for name, p in C.PRESETS.items():
        level, code, d = ev.verdict(ev.analyse(_sc(p)))
        assert (level, code) == ("success", ev.OPTIMAL) and d["cert"]["all_ok"], name


@pytest.mark.parametrize("name", [n for n, p in C.PRESETS.items() if p["net"] == "random"])
def test_random_preset_is_a_typical_draw(name):
    """Die gezeigte Karte hat eine Preisdecke nahe dem Median der 100 festen Karten (±10 %) und - bei den Karten, auf denen Greedy Paare verliert - Mehrkosten der Verbesserungswege nahe ihrem Median (±3 Punkte)."""
    p = C.PRESETS[name]
    dist = ev.distribution(p["n"], p["m"], p["reach"], p["ballung"])
    _, _, d = ev.verdict(ev.analyse(_sc(p)))
    assert abs(d["p"] - dist["p_median"]) <= 0.10 * dist["p_median"]
    ap_median = float(np.median(dist["gaps"]["Verbesserungswege ab Greedy"]))
    if p["reach"] in (40, 60, 150):
        assert abs(d["ap_edge_gap_pct"] - ap_median) <= 3.0


def test_fixed_presets_hide_the_random_controls():
    assert {n for n, p in C.PRESETS.items() if p["net"] in C.FIXED_NETS} == {"⚖️ Die billigste Kante klaut", "🔗 Pfad aus vier Punkten", "⛓️ Lange Kette"}
