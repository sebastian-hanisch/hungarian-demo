"""Ungarische Methode - die billigste unter den größtmöglichen Zuordnungen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Anders als die Fall-Demos im Portfolio (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt diese Demo EIN Verfahren - die Ungarische Methode - und lässt stattdessen das Beispiel wachsen.
Drittes Stück der Matching-Linie der "Konzepte"-Reihe, Fortsetzung der Verbesserungswege-Demo: sie behebt deren Kostenblindheit. Zwei Sichten auf denselben Ablauf: Preise und Dijkstra mit Potenzialen. Siehe README.

Lauffähig mit: streamlit run app.py
"""

import time

import streamlit as st

import hu_constants as C
import hu_evaluation as ev
from hu_algorithm import certificate
from hu_presets import (
    KEPT,
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    seed_widget,
    sync_query_params,
)
from hu_scenario import build
from hu_visualization import build_delta_map, build_gap_compare, build_marginal, build_path_map, build_price_map, build_reach_sweep, build_scaling

st.set_page_config(page_title="Ungarische Methode – Sebastian Hanisch", layout="wide")


def _pct(x, digits=0):
    return "–" if x is None else f"{x:.{digits}f} %".replace(".", ",")


def _share(x):
    """Anteil (0..1) als 'nn %'."""
    return f"{100 * x:.0f} %"


def _f(x, digits=1):
    return "–" if x is None else f"{x:.{digits}f}".replace(".", ",")


def _int(x):
    """Ganzzahl mit Leerzeichen als Tausendertrenner."""
    return f"{x:,.0f}".replace(",", " ")


def _path_text(path):
    """'+F1–A1, −F2–A1, ...': + wird gewählt, − wird freigegeben."""
    return ", ".join(f"{'+' if kind == 'add' else '−'}F{i + 1}–A{j + 1}" for i, j, kind in path)


@st.cache_resource(show_spinner=False, max_entries=16)
def _analysis(params):
    return ev.analyse(build(*params))


@st.cache_data(show_spinner=False)
def _distribution(n, m, reach, ballung):
    return ev.distribution(n, m, reach, ballung)


@st.cache_data(show_spinner=False)
def _effort(n, m, reach, ballung):
    return ev.effort_table(n, m, reach, ballung)


@st.cache_data(show_spinner=False)
def _reach_sweep(n, m, ballung):
    return ev.reach_sweep(n, m, ballung)


@st.cache_data(show_spinner=False)
def _scaling():
    return ev.scaling()


st.title("🧮 Ungarische Methode – die billigste unter den größtmöglichen Zuordnungen")
st.markdown(
    """
Die Verbesserungswege machen die **Paarzahl** größtmöglich, aber sie **kennen die Kosten nicht**: bei Reichweite 40 liegen sie im Median 8 % (ab Greedy) bis 36 % (ab leerem Start) über dem Optimum.
Die **Ungarische Methode** behebt das: sie findet in jeder Runde den **billigsten** Verbesserungsweg - einen kürzesten Weg auf reduzierten Kosten - und hält dabei **Preise** (Potenziale) für alle Fahrzeuge und Aufträge, die zeigen, warum kein billigeres Matching existiert.
Dieselbe Rechnung lässt sich auf zwei Arten lesen: als **Preise**, die steigen, wo mehrere Fahrzeuge denselben Auftrag wollen, und als **Dijkstra mit Potenzialen** (Johnsons Umgewichtung, nach jedem Umklappen neu gepflegt). Beide Sichten sind hier zuschaltbar.
Der Preis der Optimalität ist Aufwand: das Verfahren durchsucht ein Vielfaches der Kanten.
"""
)
st.caption(
    "Anders als die Fall-Demos im Portfolio, die an einem Anwendungsfall mehrere Verfahren vergleichen, zeigt diese Demo - drittes Stück der Matching-Linie der \"Konzepte\"-Reihe, Fortsetzung der Verbesserungswege-Demo - **ein** Verfahren an einem wachsenden Beispiel. "
    "Die Schwächen dieses Stücks sind die Ansatzpunkte der nächsten: **Auktionsalgorithmus** (dezentral, mit Geboten), **Blossom** und **Gewichteter Blossom** (allgemeine Graphen), **Gale–Shapley** (Vorlieben statt Kosten) und **Online-Matching** - alle inzwischen gebaut. "
    "Die Referenz \"Optimum\" kommt aus der kleinen exakten Lösung der Greedy-Matching-Demo, die hier nur zur Gegenprobe dient."
)

with st.expander("So funktioniert die Ungarische Methode", expanded=True):
    st.markdown(
        """
1. **Preise:** jeder Auftrag hat einen *Preis* p, jedes Fahrzeug einen *Gewinn* g (am Anfang alle 0). Für jedes mögliche Paar gilt: Preis − Gewinn ≤ Kosten; bei gewählten Paaren gilt Gleichheit („straff“). Ein Fahrzeug „will“ den Auftrag mit der besten Prämie, Preis minus Anfahrtskosten.
2. **Eine Runde:** von allen freien Fahrzeugen aus wird der **billigste Verbesserungsweg** zu einem freien Auftrag gesucht - ein Dijkstra auf den *reduzierten* Kosten Kosten + g − p, die nie negativ sind. Die Suche endet, sobald ein freier Auftrag erreicht ist.
3. **Preise steigen:** jede festgelegte Ecke steigt um ihren Abstand, alle anderen um den Abstand des Ziels (**min(Abstand, Abstand zum Ziel)**). Danach sind gewählte Kanten weiter straff und keine Kante hat negativen Schlupf.
4. **Umklappen:** wie bei den Verbesserungswegen; jede Runde kostet **Grenzkosten** - so viel mehr, wie das neue Paar kostet - und diese steigen von Runde zu Runde.
5. **Beweis:** wenn kein freier Auftrag mehr erreichbar ist, belegen die Preise, dass kein Matching mit gleich vielen Paaren billiger ist (Dualzulässigkeit, keine negativen Tauschkreise).
        """
    )

st.caption("🎯 Schnellstart – eine Beispielkarte laden:")
names = list(C.PRESETS.keys())
for row in range(0, len(names), 4):
    preset_cols = st.columns(4)
    for col, name in zip(preset_cols, names[row:row + 4]):
        with col:
            st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name])

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    net_key = st.selectbox(
        "Karte", list(C.NETS), key="net_select", format_func=lambda k: C.NETS[k],
        help="Eine zufällige Karte mit Fahrzeugen und Aufträgen, oder eine der festen Lehrbuchkarten, an denen sich die Rechnung von Hand nachvollziehen lässt (die lange Kette zeigt, was „Paare zuerst“ kostet).",
    )
    if net_key == "random":
        seed_widget("n_slider")
        n = st.slider("Fahrzeuge", *bounds("n_slider"), key="n_slider", help="Anzahl der Fahrzeuge.")
        st.session_state[KEPT["n_slider"]] = n
        seed_widget("m_slider")
        m = st.slider("Aufträge", *bounds("m_slider"), key="m_slider", help="Anzahl der Aufträge.")
        st.session_state[KEPT["m_slider"]] = m
        seed_widget("reach_slider")
        reach = st.slider(
            "Reichweite [min]", *bounds("reach_slider"), key="reach_slider", step=5,
            help="Wie weit ein Fahrzeug höchstens fahren darf. Die Ungarische Methode durchsucht bei 10 im Mittel 51 Kanten (Verbesserungswege ab Greedy: 3), bei 40 sind es 1 698 (140), bei 150 5 322 - dort hat Greedy schon die größtmögliche Paarzahl.",
        )
        st.session_state[KEPT["reach_slider"]] = reach
        seed_widget("ballung_slider")
        ballung = st.slider("Ballung [%]", *bounds("ballung_slider"), key="ballung_slider", step=25, help="0 = Fahrzeuge und Aufträge gleichmäßig verteilt, 100 = alle um drei Stadtteile gruppiert.")
        st.session_state[KEPT["ballung_slider"]] = ballung
        seed_widget("seed_input")
        seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
        st.session_state[KEPT["seed_input"]] = seed
        st.button("🎲 Neue Karte generieren", width="stretch", on_click=randomize_seed, help="Würfelt einen neuen Zufalls-Seed. Die Verteilung über 100 feste Karten weiter unten ändert sich dabei nicht.")
    else:
        n = int(st.session_state.get(KEPT["n_slider"], C.DEFAULT_N))
        m = int(st.session_state.get(KEPT["m_slider"], C.DEFAULT_M))
        reach = int(st.session_state.get(KEPT["reach_slider"], C.DEFAULT_REACH))
        ballung = int(st.session_state.get(KEPT["ballung_slider"], C.DEFAULT_BALLUNG))
        seed = int(st.session_state.get(KEPT["seed_input"], C.DEFAULT_SEED))
        st.caption("Diese Karte ist fest - es gibt nichts zu erzeugen. Zahl der Fahrzeuge und Aufträge, Reichweite, Ballung und Seed gehören zur zufälligen Karte.")

# feste Karten ignorieren die Zufallsregler: sonst würden gleiche Karten unter verschiedenen Schlüsseln mehrfach berechnet
params = (net_key, int(n), int(m), int(reach), int(ballung), int(seed))
if net_key in C.FIXED_NETS:
    params = (net_key, C.DEFAULT_N, C.DEFAULT_M, C.DEFAULT_REACH, C.DEFAULT_BALLUNG, C.DEFAULT_SEED)
with st.spinner("Rechne..."):
    a = _analysis(params)
sc, res, opt = a.scenario, a.result, a.opt
level, code, d = ev.verdict(a)
n_rounds = len(res.rounds)

# --- Die Ungarische Methode in Aktion ---------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Die Ungarische Methode in Aktion")
if st.session_state.get("hu_step_owner") != params:
    st.session_state["hu_step"] = n_rounds
    st.session_state["hu_step_owner"] = params
step_col, view_col, play_col = st.columns([4, 3, 2])
with step_col:
    if n_rounds > 0:
        step = st.slider("Runde", 0, n_rounds, key="hu_step", help="Wie viele Runden schon umgeklappt sind. Bei 0 ist der Start zu sehen, mit der Suche der ersten Runde; ganz rechts das fertige Matching und der Beweis.")
    else:
        step = 0
        st.caption("Hier gibt es keine Runde: kein Paar ist möglich.")
with view_col:
    view = st.radio("Ansicht", list(C.VIEW_LABELS), key="view_radio", format_func=lambda k: C.VIEW_LABELS[k], horizontal=True,
                    help="Dieselbe Rechnung, zwei Lesarten. Preise: Aufträge haben Preise, Fahrzeuge Gewinne, jede Runde hebt Preise an. Kürzeste Wege: jede Runde ist ein Dijkstra auf reduzierten Kosten, und das Potenzial steigt um min(Abstand, Abstand zum Ziel).")
with play_col:
    auto_play = st.button("▶️ Abspielen", width="stretch", disabled=n_rounds == 0)
sync_query_params({"net_select": net_key, "view_radio": view, "n_slider": int(n), "m_slider": int(m), "reach_slider": int(reach), "ballung_slider": int(ballung), "seed_input": int(seed)})
view_slot = st.empty()
cum_before = [0] + [sum(res.marginal[:k]) for k in range(1, n_rounds + 1)]


def _cert_table():
    cert = certificate(sc, res)
    ok = lambda b: "✅" if b else "❌"
    rows = [
        (f"C1 Gewählte Kanten straff", f"{ok(cert['c1'])} alle {res.count} Paare haben Schlupf 0"),
        ("C2 Kein negativer Schlupf", f"{ok(cert['c2'])} {cert['n_tight']} von {cert['n_edges']} möglichen Kanten straff, kleinster Schlupf der übrigen: {cert['min_slack'] if cert['min_slack'] is not None else '–'}"),
        ("C3 Freie Fahrzeuge: Gewinn 0", f"{ok(cert['c3'])} {len(res.pi_v) - res.count} freie(s) Fahrzeug(e)"),
        (f"C4 Freie Aufträge: Preis = Decke P = {cert['p']}", f"{ok(cert['c4'])} {sc.m - res.count} freie(r) Auftrag/Aufträge"),
        ("C5 Kein freier Auftrag erreichbar", f"{ok(cert['c5'])} Überdeckung mit {cert['cover_size']} Ecken = {res.count} Paare"),
        ("Kostenidentität", f"{ok(cert['identity'])} Kosten {res.cost} = Σ Preise {sum(res.pi_o)} − Σ Gewinne {sum(res.pi_v)} − ({sc.m} − {res.count}) · {res.p} = {cert['identity_rhs']}"),
    ]
    return {"Bedingung": [r[0] for r in rows], "Prüfung": [r[1] for r in rows]}


def _render(k):
    """Runde k: links der Zustand vor der nächsten Runde (mit Preisen bzw. Suche und Weg), rechts der Zustand danach; am Ende der Beweis."""
    with view_slot.container():
        c1, c2 = st.columns(2)
        if k < n_rounds:
            rnd = res.rounds[k]
            if view == "prices":
                c1.markdown(f"**Vor Runde {k + 1}** - Preise und Gewinne, der billigste Weg ({rnd.length} Kanten)")
                c1.plotly_chart(build_price_map(sc, res.states[k], rnd.pi_v_before, rnd.pi_o_before, res.p, rnd.path), width="stretch", key=f"map_before_prices_{k}")
                c2.markdown(f"**Nach Runde {k + 1}** - Preise steigen (Zahl an der Ecke: Anstieg), {rnd.pairs_after} Paare")
            else:
                c1.markdown(f"**Vor Runde {k + 1}** - Dijkstra: Zahl an der Ecke = reduzierter Abstand, Farbe = Reihenfolge des Festlegens")
                c1.plotly_chart(build_path_map(sc, res.states[k], rnd), width="stretch", key=f"map_before_paths_{k}")
                c2.markdown(f"**Nach Runde {k + 1}** - Potenziale steigen um min(Abstand, {rnd.d_t}), {rnd.pairs_after} Paare")
            c2.plotly_chart(build_delta_map(sc, res.states[k + 1], rnd), width="stretch", key=f"map_after_{k}")
            st.caption(f"Weg dieser Runde: {_path_text(rnd.path)} (+ wird gewählt, − wird freigegeben). Die Suche hat {rnd.scanned} Kanten durchsucht und {len(rnd.settled)} Ecken festgelegt; "
                       f"das neue Paar kostet **{rnd.w} Minuten zusätzlich** (Grenzkosten, Abstand zum Ziel {rnd.d_t}, Preisdecke P: {rnd.p_before} → {rnd.p_after}).")
            if view == "paths":
                shown = rnd.settled[:25]
                st.table({"Rang": [r + 1 for _k, _x, _d, r in shown], "Ecke": [("F" if kk == 1 else "A") + str(x + 1) for kk, x, _d, _r in shown], "reduzierter Abstand d": [dd for _k, _x, dd, _r in shown],
                          "wahrer Abstand D = d + Potenzial vorher": [dd + (rnd.pi_v_before[x] if kk == 1 else rnd.pi_o_before[x]) for kk, x, dd, _r in shown],
                          "Potenzial steigt um min(d, d_Ziel)": [min(dd, rnd.d_t) for _k, _x, dd, _r in shown],
                          "Potenzial nachher": [(rnd.pi_v_after[x] if kk == 1 else rnd.pi_o_after[x]) for kk, x, _dd, _r in shown]})
                if len(rnd.settled) > len(shown):
                    st.caption(f"Die ersten {len(shown)} von {len(rnd.settled)} festgelegten Ecken; alle übrigen Ecken steigen um den Abstand des Ziels ({rnd.d_t}).")
        else:
            c1.markdown(f"**Ergebnis** - {res.count} Paare, {res.cost} Minuten, Preise und Gewinne am Ende")
            c1.plotly_chart(build_price_map(sc, res.pairs, res.pi_v, res.pi_o, res.p), width="stretch", key=f"map_result_{k}")
            c2.markdown("**Beweis:** die Preise belegen die Optimalität")
            c2.table(_cert_table())
            st.caption("Dunkle Linien sind straffe Kanten (Schlupf 0), blaue die gewählten. Weil kein mögliches Paar einen negativen Schlupf hat und alle gewählten straff sind, gibt es keinen Tauschkreis, der die Kosten senkt; "
                       "die Bedingungen C3 und C4 sorgen dafür, dass auch kein anderes Matching mit gleich vielen Paaren billiger ist.")


if auto_play:
    for kk in range(n_rounds + 1):
        _render(kk)
        time.sleep(min(0.8, 8.0 / max(n_rounds, 1)))
    step = n_rounds
else:
    _render(step)

if n_rounds > 0:
    st.plotly_chart(build_marginal(res.marginal), width="stretch", key="marginal_chart")
st.caption("Quadrate sind Fahrzeuge, Kreise Aufträge; ohne Partner nur als Umriss. Preise-Sicht: Auftragspreise und Fahrzeuggewinne (Größe und Farbe); freie Aufträge stehen an der Decke P. "
           "Die Grenzkosten steigen von Runde zu Runde: das letzte Paar ist das teuerste.")

st.markdown("---")

# --- Optimal - und was kostet das? ------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Optimal – und was kostet das?")
st.caption("Verglichen wird bei gleicher Paarzahl: ein Matching mit weniger Paaren ist trivial billiger. **Mehrkosten** = Kosten des Verfahrens geteilt durch die des Optimums, minus 1; das Optimum kommt aus der Referenz der Greedy-Matching-Demo (ein verwandtes Verfahren, deshalb zusätzlich in den Tests gegen scipy, networkx und Brute Force geprüft).")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Paare (Ergebnis)", f"{res.count} von {opt.count}", help="Nach dem Ende der Methode hat das Matching die größtmögliche Paarzahl.")
m2.metric("Kosten", f"{res.cost} min", delta=f"{res.cost - opt.cost:+d} min gegenüber der Referenz" if res.cost != opt.cost else "so billig wie die Referenz", delta_color="inverse" if res.cost != opt.cost else "off",
          help=f"Summe der Anfahrtszeiten. Referenz: {opt.cost} min.")
m3.metric("Grenzkosten des letzten Paars", f"{d['last_w']} min" if d["last_w"] is not None else "–", delta=f"Durchschnitt aller Runden {_f(d['mean_w'])} min" if d["mean_w"] is not None else None, delta_color="off",
          help="So viel mehr kostet das zuletzt hinzugekommene Paar. Die Grenzkosten steigen von Runde zu Runde; die Preisdecke P ist genau dieser Wert.")
m4.metric("Durchsuchte Kanten", _int(d["scanned"]), delta=f"Verbesserungswege ab Greedy: {_int(d['ap_edge_scanned'])}", delta_color="off",
          help=f"Alle Suchen zusammen, einschließlich der letzten erfolglosen; das Netz hat {d['edges']} Kanten. Maschinenunabhängig gezählt, keine Sekunden. Heap-Operationen kommen mit einem Log-Faktor hinzu ({_int(d['pops'])} Entnahmen).")

if code == "none":
    st.info("ℹ️ Keine einzige Kante ist möglich – die Reichweite ist zu klein. Es gibt nichts zuzuordnen.")
elif code == "mismatch":
    st.error(f"Abweichung von der Referenz: {res.count} Paare für {res.cost} Minuten gegen {opt.count} Paare für {opt.cost} Minuten. Das dürfte nicht vorkommen.")
else:
    others = []
    if d["greedy_gap_pct"] is not None:
        others.append(f"Greedy zahlte {d['greedy_cost']} Minuten ({_pct(d['greedy_gap_pct'])} mehr)")
    else:
        others.append(f"Greedy hatte nur {d['greedy_count']} von {d['opt_count']} Paaren")
    others.append(f"die Verbesserungswege ab Greedy {d['ap_edge_cost']} ({_pct(d['ap_edge_gap_pct'], 1)} mehr), ab leerem Start {d['ap_empty_cost']} ({_pct(d['ap_empty_gap_pct'], 1)} mehr)")
    st.success(f"✅ Optimal: {res.count} Paare für {res.cost} Minuten – genau die Referenz. {others[0]}, {others[1]}. Das letzte Paar hat {d['last_w']} Minuten zusätzlich gekostet.")

st.markdown("**Die Verfahren im Vergleich auf dieser Karte**")
cmp_rows = ev.compare_table(a)
st.table({"Verfahren": [r["label"] for r in cmp_rows], "Paare": [r["count"] for r in cmp_rows], "Kosten [min]": [r["cost"] for r in cmp_rows],
          "Mehrkosten": [(_pct(r["cost_gap_pct"], 1) if r["cost_gap_pct"] is not None else "nicht vergleichbar") for r in cmp_rows],
          "Runden": [str(r["rounds"]) if r["rounds"] is not None else "–" for r in cmp_rows], "durchsuchte Kanten": [_int(r["scanned"]) if r["scanned"] is not None else "–" for r in cmp_rows]})

if net_key in C.FIXED_NETS:
    st.info("Feste Karte: es gibt nur diese eine Ziehung. Für die Verteilung über viele Karten eine zufällige Karte wählen.")
else:
    st.markdown(f"**Nicht nur diese eine Karte:** {len(C.DIST_SEEDS)} feste Karten mit denselben Einstellungen (Fahrzeuge {n}, Aufträge {m}, Reichweite {reach}, Ballung {ballung} %), getrennt vom Seed oben.")
    dist = _distribution(int(n), int(m), int(reach), int(ballung))
    if dist["n_valid"] == 0:
        st.info("ℹ️ Bei dieser Reichweite gibt es auf keiner der Karten ein mögliches Paar.")
    else:
        med_ap = sorted(dist["gaps"]["Verbesserungswege ab Greedy"])
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Optimum getroffen", _share(dist["share_optimal"]), help="Anteil der Karten, auf denen Paarzahl und Kosten so gut sind wie beim Optimum - hier immer alle.")
        p2.metric("Durchsuchte Kanten (Mittel)", _int(dist["scanned_mean"]), delta=f"ab Greedy: {_int(dist['ap_edge_scanned_mean'])}", delta_color="off", help=f"Das Netz hat im Mittel {_int(dist['edges_mean'])} Kanten.")
        p3.metric("Mehrkosten der Verbesserungswege (Median)", _pct(med_ap[len(med_ap) // 2]) if med_ap else "–", delta="Ungarische Methode: 0 %", delta_color="off", help="Median der Mehrkosten der Verbesserungswege ab Greedy; die Ungarische Methode hat keine.")
        p4.metric("Letztes Paar gegen Durchschnitt", f"{_f(dist['last_ratio_median'])}×" if dist["last_ratio_median"] is not None else "–", help="Median über die Karten: Grenzkosten des letzten Paars geteilt durch den Durchschnitt der Grenzkosten aller Runden.")
        st.success(f"✅ Auf {_share(dist['share_optimal'])} der {dist['n_seeds']} Karten dieser Einstellung liefert die Ungarische Methode das Optimum - Mehrkosten 0. "
                   f"Der Preis: {_int(dist['scanned_mean'])} durchsuchte Kanten im Mittel, die Verbesserungswege ab Greedy brauchen {_int(dist['ap_edge_scanned_mean'])}.")
        h1, h2 = st.columns([3, 2])
        gaps_plot = {k: v for k, v in dist["gaps"].items() if v}
        cur = d["ap_edge_gap_pct"]
        h1.plotly_chart(build_gap_compare(gaps_plot, current=cur), width="stretch", key="gap_hist")
        h1.caption("Mehrkosten der Vergleichsverfahren (nur Karten mit gleicher Paarzahl wie das Optimum). Die Ungarische Methode liegt bei 0: rote Linie.")
        eff = _effort(int(n), int(m), int(reach), int(ballung))
        h2.markdown("**Aufwand und Mehrkosten** (Mittel und Median über die Karten)")
        h2.table({"Verfahren": [r["label"] for r in eff], "Paare größtmöglich": [_share(r["pairs_max"]) for r in eff], "Runden": [_f(r["rounds"]) if r["rounds"] is not None else "–" for r in eff],
                  "durchsuchte Kanten": [_int(r["scanned"]) if r["scanned"] is not None else "–" for r in eff], "Mehrkosten (Median)": [_pct(r["gap_median"], 1) for r in eff]})

st.markdown("**Wie hängt der Aufwand von der Reichweite ab?**")
if st.button("Reichweite von 10 bis 150 durchfahren (40 Karten je Wert, dauert wenige Sekunden)", key="sweep_start"):
    st.session_state["sweep_on"] = (int(n), int(m), int(ballung))
if st.session_state.get("sweep_on") == (int(n), int(m), int(ballung)):
    with st.spinner(f"Rechne {len(C.REACH_SWEEP)} Reichweiten × {len(C.SWEEP_SEEDS)} Karten..."):
        sweep_rows = _reach_sweep(int(n), int(m), int(ballung))
    st.plotly_chart(build_reach_sweep(sweep_rows, current=int(reach) if net_key == "random" else None), width="stretch", key="sweep_chart")
    st.caption("Mittel über 40 feste Karten je Reichweite; Fahrzeuge, Aufträge und Ballung wie oben. Oben in logarithmischer Skala: die Ungarische Methode durchsucht überall ein Vielfaches der Kanten der Verbesserungswege ab Greedy - "
               "bei knapper Reichweite gibt es wenig zu suchen, bei mittlerer und großer viel. Unten die Mehrkosten der Verbesserungswege: genau die Lücke, die die Ungarische Methode schließt.")

st.markdown("---")

# --- Aufwand ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Aufwand: wie wächst die Suche mit der Karte?")
if st.button("Karten von 10 bis 320 Fahrzeugen durchrechnen (dauert einige Sekunden)", key="scaling_start"):
    st.session_state["scaling_on"] = True
if st.session_state.get("scaling_on"):
    with st.spinner("Rechne 6 Kartengrößen × 10 Karten × 2 Verfahren..."):
        sc_rows = _scaling()
    c1, c2 = st.columns([3, 2])
    c1.plotly_chart(build_scaling(sc_rows), width="stretch", key="scaling_chart")
    c2.table({"Fahrzeuge = Aufträge": [r["n"] for r in sc_rows], "Reichweite": [r["reach"] for r in sc_rows], "Kanten": [_f(r["edges"], 0) for r in sc_rows], "Ungarisch": [_int(r["scanned"]) for r in sc_rows],
              "ab Greedy": [_int(r["ap_scanned"]) for r in sc_rows], "Faktor": [_f(r["scanned"] / r["ap_scanned"]) + "×" for r in sc_rows]})
    st.caption("Fahrzeuge = Aufträge bei konstantem mittleren Grad (die Reichweite sinkt mit der Wurzel der Kartengröße), Mittel über 10 feste Karten. Gezählt werden **durchsuchte Kanten**, nicht Sekunden; die Heap-Operationen kommen mit einem Log-Faktor hinzu. "
               "Beide Verfahren wachsen etwa mit dem **Quadrat** der Kartengröße (eine Suche je Paar, jede kann fast alle Kanten anfassen); die Ungarische Methode bleibt dabei bei einem festen Vielfachen der Verbesserungswege ab Greedy.")

st.markdown("---")

# --- Grenzen -----------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Es gibt einen Rechner, der alle Kosten kennt** | Die Preise entstehen in einer zentralen Rechnung über die ganze Kostenmatrix. Fahrzeuge, die nur ihre eigenen Kosten kennen und selbst bieten, kommen zum gleichen Ergebnis nur mit Geboten und einer Toleranz. | **Auktionsalgorithmus**: dezentral, mit Geboten und ε |
| **Es gibt zwei getrennte Seiten** | Fahrzeuge und Aufträge bilden zwei Gruppen. Sollen sich Fahrer untereinander paaren, gibt es Zyklen ungerader Länge, die diese Suche nicht behandelt. | **Blossom**, dann **Gewichteter Blossom** |
| **Nur die Summe der Kosten zählt** | Die Ungarische Methode minimiert die Gesamtkosten und fragt nicht, ob ein Fahrzeug lieber einen anderen Auftrag hätte. Haben beide Seiten Vorlieben, ist ein stabiles Ergebnis oft teurer als dieses Optimum. | **Gale–Shapley**: stabile Paarungen, der Preis der Stabilität gegen dieses Optimum |
| **Alles ist vorab bekannt** | Aufträge kommen hier alle vor der Rechnung an. Kommen sie nacheinander und sind schon zugesagt, darf nicht mehr umgeklappt werden. | **Online-Matching** |
| **Der Aufwand ist gleichgültig** | Die Ungarische Methode durchsucht ein Vielfaches der Kanten der Verbesserungswege: bei Reichweite 40 rund 12-mal so viele wie ab Greedy, bei 40 Fahrzeugen rund 54-mal so viele; mit der Kartengröße wächst sie etwa quadratisch. | Beschleunigungen (Hopcroft–Karp für die Paarzahl, Skalierungsverfahren für die Kosten) |
"""
)
st.caption("Die Matching-Linie ist inzwischen vollständig gebaut (13 Stücke): die Wurzel (Greedy-Matching), die Verbesserungswege, Hopcroft–Karp, Auktionsalgorithmus, Blossom, Gewichteter Blossom, Gale–Shapley, Stabile Mitbewohner, Krankenhaus-Zulassung, Top Trading Cycles, Nierentausch und Online-Matching.")

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Modell.** Bipartiter Graph mit Fahrzeugen $V$, Aufträgen $O$, möglichen Paaren $E$ und ganzzahligen Kosten $c_{ij}\ge 0$. Gesucht ist ein Matching $M$ mit **größtmöglicher Paarzahl** $\nu$ und unter allen solchen **kleinsten Kosten** $c(M)$ (lexikografisch, ohne Big-M).

**Netz.** Quelle $s\to i$ (Kosten 0), $i\to j$ (Kosten $c_{ij}$), $j\to t$ (Kosten 0), alle Kapazitäten 1. Ein Matching mit $k$ Paaren ist ein Fluss vom Wert $k$. Im Restgraphen haben nicht gewählte Paare $i\to j$ die Kosten $c_{ij}$, gewählte $j\to i$ die Kosten $-c_{ij}$.

**Successive Shortest Paths.** Klappe wiederholt einen billigsten Weg von $s$ nach $t$ um. Dann ist das Matching nach $k$ Runden das billigste mit $k$ Paaren (kein negativer Kreis im Restgraphen); endet das Verfahren, ist $k=\nu$. Die **Grenzkosten** $W_k$ (Kosten des $k$-ten Paars zusätzlich) sind nicht fallend, und $c(M)=\sum_k W_k$.

**Potenziale.** $\pi$ auf allen Ecken, $\pi_s=0$, $\pi_t=P$. Reduzierte Kosten $r=w+\pi_a-\pi_b\ge 0$ auf allen Restkanten. Jede Runde: ein Dijkstra von allen freien Fahrzeugen mit Abstand 0 auf $r$, Abbruch beim ersten freien Auftrag (Abstand $d_t$). Dann
$$\pi_x \mathrel{+}= \min(d_x,\,d_t),\qquad P \mathrel{+}= d_t,\qquad W = d_t + P_{\text{alt}},$$
mit $\min(d_x,d_t)=d_t$ für alle nicht festgelegten Ecken. Das ist Johnsons Umgewichtung, nach jedem Umklappen neu gepflegt. Invarianten: freie Fahrzeuge haben $\pi=0$, freie Aufträge $\pi=P$, gewählte Kanten sind straff, alle Restkanten haben $r\ge 0$, und $P$ ist die Grenzkosten des letzten Paars.

**Preise.** Mit $p_j=\pi_j$ (Preis des Auftrags) und $g_i=\pi_i$ (Gewinn des Fahrzeugs) lautet die Zulässigkeit $p_j-g_i\le c_{ij}$ für alle möglichen Paare, mit Gleichheit auf gewählten. Das ist das duale Problem der Zuordnung; $u=-g$, $v=p$ ergibt $u_i+v_j\le c_{ij}$.

**Beweis.** Am Ende gelten: (C1) gewählte Kanten straff, (C2) $p_j-g_i\le c_{ij}$ überall, (C3) freie Fahrzeuge $g=0$ und alle $g\ge 0$, (C4) freie Aufträge $p=P$ und alle $p\le P$, (C5) kein freier Auftrag erreichbar (Überdeckung mit $|M|$ Ecken). Das ist Dualzulässigkeit des gesamten Netzes inklusive $s$ und $t$; nach schwacher Dualität kostet jedes Matching mit $\nu$ Paaren mindestens so viel wie $M$. Kostenidentität: $c(M)=\sum_j p_j-\sum_i g_i-(|O|-\nu)\,P$.

**Aufwand.** Eine Runde ist ein Dijkstra in $O(|E|\log|V|)$, es gibt $\nu$ Runden: $O(\nu\,|E|\log|V|)$, bei dichten Graphen $O(n^3)$. Gemessen werden durchsuchte Kanten; Heap-Operationen kommen mit einem Log-Faktor hinzu.

**Grenzen.** (1) Zentral, alle Kosten bekannt. (2) Zwei Seiten. (3) Nur die Summe der Kosten zählt. (4) Alles vorab bekannt. (5) Aufwand.

Implementiert in `hu_scenario.py` (Karten, eigener Zufallsgenerator), `hu_greedy.py` und `hu_augment.py` (Greedy, Referenz und Verbesserungswege aus den Vorgängerdemos), `hu_algorithm.py` (Ungarische Methode, Beweis), `hu_evaluation.py` (Kennzahlen, Verteilung, Aufwand).
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
