"""Plotly-Abbildungen der Ungarischen Methode: Preise, Kürzeste Wege (Dijkstra), Grenzkosten, Verteilungen, Reichweite-Sweep und Aufwand.
Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht zoomen. Punkte auf einer Geraden werden mit Bögen gezeichnet."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import hu_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.08), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _collinear(sc):
    """Liegen alle Punkte auf einer Geraden? Dann würden sich die Paar-Linien überdecken - sie werden gebogen gezeichnet."""
    pts = list(sc.vehicles + sc.orders)
    (x0, y0), (x1, y1) = pts[0], next((p for p in pts if p != pts[0]), pts[0])
    return all((x1 - x0) * (y - y0) - (y1 - y0) * (x - x0) == 0 for x, y in pts)


def _edge_path(sc, i, j, curved, steps=14):
    """Punkte einer Paar-Linie: gerade, oder (bei Punkten auf einer Geraden) als Bogen, dessen Seite je Paar wechselt."""
    (vx, vy), (ox, oy) = sc.vehicles[i], sc.orders[j]
    if not curved:
        return [vx, ox], [vy, oy]
    dx, dy = ox - vx, oy - vy
    side = 1 if (i + j) % 2 == 0 else -1
    cx, cy = (vx + ox) / 2 - side * 0.35 * dy, (vy + oy) / 2 + side * 0.35 * dx      # Kontrollpunkt senkrecht zur Verbindung
    ts = [k / steps for k in range(steps + 1)]
    return ([(1 - t) ** 2 * vx + 2 * (1 - t) * t * cx + t * t * ox for t in ts], [(1 - t) ** 2 * vy + 2 * (1 - t) * t * cy + t * t * oy for t in ts])


def _segments(sc, pairs, curved=False):
    """Linienspur für eine Menge von Paaren (None trennt die Segmente)."""
    x, y = [], []
    for i, j in pairs:
        px, py = _edge_path(sc, i, j, curved)
        x += px + [None]
        y += py + [None]
    return x, y


def _feasible_pairs(sc):
    return [(i, j) for i in range(sc.n) for j in range(sc.m) if sc.feasible[i, j]]


def _map_layout(fig, sc, height):
    xs = [p[0] for p in sc.vehicles + sc.orders]
    ys = [p[1] for p in sc.vehicles + sc.orders]
    pad = 8
    if _collinear(sc):
        # Punkte auf einer Geraden: nur die Bögen brauchen Höhe. Das Seitenverhältnis wird freigegeben, sonst wird eine lange Kette zu einem dünnen Streifen.
        span = max(max(xs) - min(xs), max(ys) - min(ys), 1)
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        if max(xs) - min(xs) >= max(ys) - min(ys):
            fig.update_xaxes(visible=False, range=[min(xs) - pad, max(xs) + pad])
            fig.update_yaxes(visible=False, range=[cy - span * 0.22, cy + span * 0.22])
        else:
            fig.update_xaxes(visible=False, range=[cx - span * 0.22, cx + span * 0.22])
            fig.update_yaxes(visible=False, range=[min(ys) - pad, max(ys) + pad])
        return _base(fig, min(height, 320))
    fig.update_xaxes(visible=False, range=[min(xs) - pad, max(xs) + pad], scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False, range=[min(ys) - pad, max(ys) + pad])
    return _base(fig, height)


def _scaled(values, vmax, lo, hi):
    return [lo + (hi - lo) * min(v, vmax) / vmax if vmax else lo for v in values]


def _base_edges(fig, sc, curved, pairs, path=None, slack=None):
    """Blasse mögliche Paare (bei bekanntem Schlupf: straffe Kanten dunkel), gewählte Paare blau, Verbesserungsweg grün / rot gestrichelt."""
    feas = _feasible_pairs(sc)
    if slack is None:
        ex, ey = _segments(sc, feas, curved)
        fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color="rgba(150,150,150,0.35)", width=1), hoverinfo="skip", name="mögliche Paare"))
    else:
        pset = set(pairs)
        tight = [e for e in feas if slack[e] == 0 and e not in pset]
        rest = [e for e in feas if slack[e] != 0]
        rx, ry = _segments(sc, rest, curved)
        fig.add_trace(go.Scatter(x=rx, y=ry, mode="lines", line=dict(color="rgba(150,150,150,0.30)", width=1), hoverinfo="skip", name="mit Schlupf"))
        tx, ty = _segments(sc, tight, curved)
        fig.add_trace(go.Scatter(x=tx, y=ty, mode="lines", line=dict(color=C.COLORS["tight"], width=1.8), hoverinfo="skip", name="straff (Schlupf 0)"))
    dropped = {(i, j) for i, j, kind in path if kind == "drop"} if path else set()
    added = [(i, j) for i, j, kind in path if kind == "add"] if path else []
    kx, ky = _segments(sc, [p for p in pairs if p not in dropped], curved)
    fig.add_trace(go.Scatter(x=kx, y=ky, mode="lines", line=dict(color=C.COLORS["matched"], width=3.5), hoverinfo="skip", name="gewählt"))
    if path:
        dx, dy = _segments(sc, sorted(dropped), curved)
        fig.add_trace(go.Scatter(x=dx, y=dy, mode="lines", line=dict(color=C.COLORS["drop"], width=4.5, dash="dash"), hoverinfo="skip", name="wird freigegeben"))
        ax, ay = _segments(sc, added, curved)
        fig.add_trace(go.Scatter(x=ax, y=ay, mode="lines", line=dict(color=C.COLORS["add"], width=4.5), hoverinfo="skip", name="wird gewählt"))
    return added


def build_price_map(sc, pairs, pi_v, pi_o, p_max, path=None, height=430):
    """Preise-Sicht: Aufträge nach Preis (Größe und Farbe, freie Aufträge stehen an der Decke P), Fahrzeuge nach Gewinn g = pi; straffe Kanten dunkel."""
    curved = _collinear(sc)
    slack = {(i, j): int(sc.cost[i, j]) - (pi_o[j] - pi_v[i]) for i, j in _feasible_pairs(sc)}
    fig = go.Figure()
    _base_edges(fig, sc, curved, pairs, path, slack)
    matched_v = {i for i, _ in pairs}
    matched_o = {j for _, j in pairs}
    small = sc.n + sc.m <= 24
    vmax = max(p_max, 1)
    for kind, pts, pis, matched, symbol, scale, prefix, tpos in (("Fahrzeug", sc.vehicles, pi_v, matched_v, "square", "Greens", "F", "top center"),
                                                                  ("Auftrag", sc.orders, pi_o, matched_o, "circle", "Oranges", "A", "bottom center")):
        for on in (True, False):
            idx = [k for k in range(len(pts)) if (k in matched) == on]
            if not idx:
                continue
            values = [pis[k] for k in idx]
            what = "Gewinn" if kind == "Fahrzeug" else "Preis"
            hover = [f"{kind} {k + 1}: {what} {pis[k]}" + ("" if on else " (frei)") for k in idx]
            fig.add_trace(go.Scatter(
                x=[pts[k][0] for k in idx], y=[pts[k][1] for k in idx], mode="markers+text" if small else "markers", name=f"{kind} {'mit' if on else 'ohne'} Partner",
                text=[f"{prefix}{k + 1}: {pis[k]}" for k in idx] if small else None, textposition=tpos, hovertext=hover, hoverinfo="text",
                marker=dict(symbol=symbol if on else symbol + "-open", size=_scaled(values, vmax, 9, 20), color=values, colorscale=scale, cmin=0, cmax=vmax, line=dict(width=2, color="#333"))))
    return _map_layout(fig, sc, height)


def build_path_map(sc, pairs, rnd, height=430):
    """Kürzeste-Wege-Sicht: die von der Suche festgelegten Ecken nach Rang eingefärbt (Beschriftung: reduzierter Abstand), Vorgängerbaum, Zielauftrag umringt, Weg grün / rot."""
    curved = _collinear(sc)
    fig = go.Figure()
    _base_edges(fig, sc, curved, pairs, rnd.path)
    tx, ty = _segments(sc, [(i, j) for i, j in rnd.tree], curved)
    fig.add_trace(go.Scatter(x=tx, y=ty, mode="lines", line=dict(color="rgba(60,60,60,0.75)", width=1.6, dash="dot"), hoverinfo="skip", name="Vorgängerbaum"))
    rank = {(k, x): (r, d) for k, x, d, r in rnd.settled}
    top = max(len(rnd.settled) - 1, 1)
    small = sc.n + sc.m <= 24
    for kind, code, pts, symbol, prefix, tpos in (("Fahrzeug", 1, sc.vehicles, "square", "F", "top center"), ("Auftrag", 0, sc.orders, "circle", "A", "bottom center")):
        on = [k for k in range(len(pts)) if (code, k) in rank]
        off = [k for k in range(len(pts)) if (code, k) not in rank]
        if off:
            fig.add_trace(go.Scatter(x=[pts[k][0] for k in off], y=[pts[k][1] for k in off], mode="markers+text" if small else "markers", name=f"{kind} nicht festgelegt",
                                     text=[f"{prefix}{k + 1}" for k in off] if small else None, textposition=tpos, hovertext=[f"{kind} {k + 1}: nicht festgelegt" for k in off], hoverinfo="text",
                                     marker=dict(symbol=symbol + "-open", size=10, color="#999", line=dict(width=2, color="#999"))))
        if on:
            fig.add_trace(go.Scatter(x=[pts[k][0] for k in on], y=[pts[k][1] for k in on], mode="markers+text" if small else "markers", name=f"{kind} festgelegt",
                                     text=[f"{prefix}{k + 1}: {rank[(code, k)][1]}" for k in on] if small else None, textposition=tpos,
                                     hovertext=[f"{kind} {k + 1}: Rang {rank[(code, k)][0] + 1}, reduzierter Abstand {rank[(code, k)][1]}" for k in on], hoverinfo="text",
                                     marker=dict(symbol=symbol, size=12, color=[rank[(code, k)][0] for k in on], colorscale="Viridis", cmin=0, cmax=top, line=dict(width=1.5, color="#222"))))
    j_end = rnd.path[-1][1]
    fig.add_trace(go.Scatter(x=[sc.orders[j_end][0]], y=[sc.orders[j_end][1]], mode="markers", name=f"Ziel (Abstand {rnd.d_t})", hoverinfo="skip",
                             marker=dict(symbol="circle-open", size=26, color=C.COLORS["drop"], line=dict(width=3, color=C.COLORS["drop"]))))
    return _map_layout(fig, sc, height)


def build_delta_map(sc, pairs, rnd, height=430):
    """Zustand nach der Runde: gewählte Paare blau, Ecken nach Potenzialanstieg (Beschriftung +Delta)."""
    curved = _collinear(sc)
    fig = go.Figure()
    _base_edges(fig, sc, curved, pairs)
    dv = [a - b for a, b in zip(rnd.pi_v_after, rnd.pi_v_before)]
    do = [a - b for a, b in zip(rnd.pi_o_after, rnd.pi_o_before)]
    top = max(max(dv, default=0), max(do, default=0), 1)
    small = sc.n + sc.m <= 24
    for kind, pts, delta, symbol, prefix, tpos, matched in (("Fahrzeug", sc.vehicles, dv, "square", "F", "top center", {i for i, _ in pairs}),
                                                              ("Auftrag", sc.orders, do, "circle", "A", "bottom center", {j for _, j in pairs})):
        for on in (True, False):
            idx = [k for k in range(len(pts)) if (k in matched) == on]
            if idx:
                fig.add_trace(go.Scatter(x=[pts[k][0] for k in idx], y=[pts[k][1] for k in idx], mode="markers+text" if small else "markers", name=f"{kind} {'mit' if on else 'ohne'} Partner",
                                         text=[f"{prefix}{k + 1}: +{delta[k]}" for k in idx] if small else None, textposition=tpos,
                                         hovertext=[f"{kind} {k + 1}: Potenzial +{delta[k]}" for k in idx], hoverinfo="text",
                                         marker=dict(symbol=symbol if on else symbol + "-open", size=11, color=[delta[k] for k in idx], colorscale="Blues", cmin=0, cmax=top, line=dict(width=2, color="#333"))))
    return _map_layout(fig, sc, height)


def build_marginal(marginal, height=280):
    """Grenzkosten je Runde (Balken: das neue Paar kostet so viel zusätzlich) und kumulierte Kosten (Linie)."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    rounds = list(range(1, len(marginal) + 1))
    cum = [sum(marginal[:k]) for k in rounds]
    fig.add_trace(go.Bar(x=rounds, y=list(marginal), name="Grenzkosten des neuen Paars [min]", marker_color=C.COLORS["add"], opacity=0.6), secondary_y=False)
    fig.add_trace(go.Scatter(x=rounds, y=cum, mode="lines+markers", name="Kosten insgesamt [min]", line=dict(color=C.COLORS["matched"])), secondary_y=True)
    fig.update_xaxes(title="Runde", dtick=1 if len(rounds) <= 25 else None)
    fig.update_yaxes(title="Grenzkosten", secondary_y=False, rangemode="tozero")
    fig.update_yaxes(title="insgesamt", secondary_y=True, rangemode="tozero", showgrid=False)
    return _base(fig, height)


def build_gap_compare(gaps_by_label, current=None, height=320):
    """Mehrkosten der Vergleichsverfahren gegenüber dem Optimum, übereinandergelegt; die Ungarische Methode liegt bei 0."""
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd"]
    fig = go.Figure()
    for k, (label, gaps) in enumerate(gaps_by_label.items()):
        fig.add_trace(go.Histogram(x=gaps, xbins=dict(size=5), name=label, marker_color=colors[k % 4], opacity=0.6))
    fig.update_layout(barmode="overlay")
    fig.add_vline(x=0, line=dict(color=C.COLORS["hungarian"], width=3), annotation_text="Ungarische Methode: 0", annotation_position="top right")
    if current is not None:
        fig.add_vline(x=current, line=dict(color="#555", dash="dash"), annotation_text="Ihre Ziehung (ab Greedy)", annotation_position="top")
    fig.update_xaxes(title="Mehrkosten gegenüber dem Optimum [%]")
    fig.update_yaxes(title="Karten")
    fig = _base(fig, height)
    fig.update_layout(legend=dict(orientation="h", y=-0.4), margin=dict(l=10, r=10, t=10, b=10), height=height + 60)
    return fig


def build_reach_sweep(rows, current=None, height=420):
    """Oben: durchsuchte Kanten der Ungarischen Methode und der Verbesserungswege ab Greedy (logarithmisch); unten: mediane Mehrkosten der Verbesserungswege."""
    x = [r["x"] for r in rows]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                        subplot_titles=("Durchsuchte Kanten (Mittel)", "Mehrkosten der Verbesserungswege ab Greedy (Median); Ungarische Methode: 0"))
    fig.add_trace(go.Scatter(x=x, y=[r["scanned"] for r in rows], mode="lines+markers", name="Ungarische Methode", line=dict(color=C.COLORS["hungarian"])), row=1, col=1)
    fig.add_trace(go.Scatter(x=x, y=[max(r["ap_scanned"], 0.5) if r["ap_scanned"] is not None else None for r in rows], mode="lines+markers", name="Verbesserungswege ab Greedy",
                             line=dict(color=C.COLORS["add"])), row=1, col=1)
    fig.add_trace(go.Scatter(x=x, y=[r["ap_gap"] for r in rows], mode="lines+markers", name="Mehrkosten [%]", line=dict(color=C.COLORS["matched"]), showlegend=False), row=2, col=1)
    if current is not None and min(x) <= current <= max(x):
        fig.add_vline(x=current, line=dict(color="#555", dash="dot"))
    fig.update_xaxes(title="Reichweite [min]", row=2, col=1)
    fig.update_yaxes(title="Kanten", type="log", row=1, col=1)
    fig.update_yaxes(title="%", row=2, col=1)
    fig = _base(fig, height)
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.2))
    return fig


def build_scaling(rows, height=340):
    """Durchsuchte Kanten gegen die Kartengröße (doppelt logarithmisch): Ungarische Methode, Verbesserungswege ab Greedy, Kanten des Graphen."""
    fig = go.Figure()
    ns = [r["n"] for r in rows]
    fig.add_trace(go.Scatter(x=ns, y=[r["scanned"] for r in rows], mode="lines+markers", name="Ungarische Methode", line=dict(color=C.COLORS["hungarian"])))
    fig.add_trace(go.Scatter(x=ns, y=[r["ap_scanned"] for r in rows], mode="lines+markers", name="Verbesserungswege ab Greedy", line=dict(color=C.COLORS["add"])))
    fig.add_trace(go.Scatter(x=ns, y=[r["edges"] for r in rows], mode="lines+markers", name="Kanten des Graphen", line=dict(color="#555", dash="dashdot")))
    fig.update_xaxes(title="Fahrzeuge = Aufträge", type="log")
    fig.update_yaxes(title="durchsuchte Kanten", type="log")
    return _base(fig, height)
