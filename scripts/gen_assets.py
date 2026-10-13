"""Genere les SVG animes du profil de l'organisation ViscoCrowd.

Tout est calcule : trajectoires des agents (graine fixe), courbe de Weidmann
(constantes du projet), sortie reelle de `viscocrowd valider-moteur`.
"""

import math
import random
import sys
from pathlib import Path
from xml.sax.saxutils import escape

SORTIE = Path(sys.argv[1])
SORTIE.mkdir(parents=True, exist_ok=True)

POLICE = "ui-sans-serif, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'Cascadia Code', Consolas, Menlo, monospace"
FOND = "#0b1220"


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


# --------------------------------------------------------------------------
# Outils de trajectoire : Catmull-Rom -> Bezier cubiques, longueurs echantillonnees
# --------------------------------------------------------------------------


def bezier_segments(points):
    pts = [points[0], *points, points[-1]]
    segs = []
    for k in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[k - 1], pts[k], pts[k + 1], pts[k + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        segs.append((p1, c1, c2, p2))
    return segs


def longueur(seg, n=40):
    a, b, c, d = seg
    total, prec = 0.0, a
    for i in range(1, n + 1):
        t = i / n
        u = 1 - t
        x = u**3 * a[0] + 3 * u * u * t * b[0] + 3 * u * t * t * c[0] + t**3 * d[0]
        y = u**3 * a[1] + 3 * u * u * t * b[1] + 3 * u * t * t * c[1] + t**3 * d[1]
        total += math.hypot(x - prec[0], y - prec[1])
        prec = (x, y)
    return total


def chemin(segs):
    a = segs[0][0]
    d = [f"M{f(a[0])} {f(a[1])}"]
    for _, c1, c2, p in segs:
        d.append(f"C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p[0])} {f(p[1])}")
    return " ".join(d)


# --------------------------------------------------------------------------
# 1. Banniere : evacuation animee de la piscine
# --------------------------------------------------------------------------


def banniere():
    rng = random.Random(20262027)
    L, H = 1200, 520
    porte_y = 310
    agents = []
    for k in range(30):
        sx, sy = rng.uniform(85, 465), rng.uniform(180, 468)
        sortie = rng.choices(["echelle1", "echelle2", "rebord"], weights=[3, 3, 4])[0]
        if sortie == "echelle1":
            cy, pause, couleur = 228, 0.6, "#ffffff"
        elif sortie == "echelle2":
            cy, pause, couleur = 412, 0.6, "#ffffff"
        else:
            cy, pause, couleur = min(max(sy + rng.uniform(-25, 25), 185), 465), 1.3, "#e0f2fe"
        # Sur le carrelage mouille, l'agent regule mal sa trajectoire : il depasse sa cible.
        wy = cy * 0.55 + porte_y * 0.45 + rng.uniform(-38, 38)
        p = [
            (sx, sy),
            (500, cy),
            (655 + rng.uniform(-25, 40), wy),
            (835, porte_y + (wy - porte_y) * 0.72),
            (1098, porte_y + rng.uniform(-11, 11)),
            (1150, porte_y + rng.uniform(-7, 7)),
            (1222, porte_y + rng.uniform(-6, 6)),
        ]
        segs = bezier_segments(p)
        lg = [longueur(s) for s in segs]
        vitesses = [0.38, 0.85, 1.05, 1.3, 0.34, 1.4]  # eau, mouille, mouille, sec, goulot, sortie
        temps = [lg[i] / vitesses[i] for i in range(len(segs))]
        total_l = sum(lg)
        # Pause au franchissement : le rebord est lent, l'echelle rapide (spec 2.7).
        pause_t = pause * 60
        t_total = sum(temps) + pause_t
        kp, kt, acc_l, acc_t = [0.0], [0.0], 0.0, 0.0
        for i in range(len(segs)):
            acc_l += lg[i]
            acc_t += temps[i]
            kp.append(acc_l / total_l)
            kt.append(acc_t / t_total)
            if i == 0:
                acc_t += pause_t
                kp.append(acc_l / total_l)
                kt.append(acc_t / t_total)
        kp[-1], kt[-1] = 1.0, 1.0
        dur = t_total / 62
        debut = -rng.uniform(0, dur)
        agents.append((chemin(segs), kp, kt, dur, debut, couleur))

    o = []
    o.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L} {H}" width="{L}" height="{H}" '
        'role="img" aria-label="Illustration animee : des agents quittent une piscine par le rebord '
        'et les echelles, traversent une plage mouillee et convergent vers une sortie unique.">'
    )
    o.append(f"""<defs>
  <linearGradient id="ciel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0f172a"/><stop offset="1" stop-color="{FOND}"/></linearGradient>
  <linearGradient id="eau" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b4fb3"/><stop offset=".55" stop-color="#0a6aa8"/><stop offset="1" stop-color="#0e7490"/></linearGradient>
  <linearGradient id="titre" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffffff"/><stop offset=".55" stop-color="#bae6fd"/><stop offset="1" stop-color="#38bdf8"/></linearGradient>
  <radialGradient id="foule" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#fb923c" stop-opacity=".75"/><stop offset="1" stop-color="#fb923c" stop-opacity="0"/></radialGradient>
  <linearGradient id="couloir" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#22c55e" stop-opacity=".55"/><stop offset="1" stop-color="#22c55e" stop-opacity="0"/></linearGradient>
  <pattern id="mouille" width="13" height="13" patternUnits="userSpaceOnUse" patternTransform="rotate(35)"><line x1="0" y1="0" x2="0" y2="13" stroke="#38bdf8" stroke-opacity=".16" stroke-width="2"/></pattern>
  <pattern id="carreaux" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M30 0H0V30" fill="none" stroke="#ffffff" stroke-opacity=".05"/></pattern>
  <clipPath id="bassin"><rect x="50" y="150" width="450" height="340" rx="18"/></clipPath>
  <filter id="halo" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="lueur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>
</defs>""")
    o.append(f'<rect width="{L}" height="{H}" rx="22" fill="url(#ciel)"/>')

    # En-tete
    o.append(
        f'<text x="58" y="80" font-family="{POLICE}" font-size="58" font-weight="800" '
        'fill="url(#titre)" letter-spacing="-1">ViscoCrowd</text>'
    )
    o.append(
        f'<text x="61" y="113" font-family="{POLICE}" font-size="19" fill="#94a3b8">'
        "Évacuation d’une piscine en panique · simulation particulaire</text>"
    )
    puces = ["R5.12 · Modélisation mathématique", "BUT 3 Informatique", "2026 – 2027"]
    x = 1142
    for texte in reversed(puces):
        larg = 12 + 7.6 * len(texte)
        x -= larg
        o.append(
            f'<rect x="{f(x)}" y="58" width="{f(larg)}" height="30" rx="15" fill="#0f2740" '
            'stroke="#1e4e7a"/>'
        )
        o.append(
            f'<text x="{f(x + larg / 2)}" y="78" text-anchor="middle" font-family="{POLICE}" '
            f'font-size="13" fill="#7dd3fc">{escape(texte)}</text>'
        )
        x -= 10

    # Zone seche et goulot
    o.append('<rect x="790" y="150" width="360" height="340" fill="#15161c"/>')
    o.append('<rect x="790" y="150" width="360" height="340" fill="url(#carreaux)"/>')
    o.append('<polygon points="790,150 1060,262 1150,290 1150,150" fill="#070b12"/>')
    o.append('<polygon points="790,490 1060,358 1150,330 1150,490" fill="#070b12"/>')
    o.append('<rect x="1150" y="290" width="50" height="40" fill="url(#couloir)"/>')
    o.append(
        '<circle cx="1112" cy="310" r="78" fill="url(#foule)">'
        '<animate attributeName="opacity" values=".35;.8;.35" dur="2.6s" repeatCount="indefinite"/></circle>'
    )
    o.append(
        '<polyline points="790,150 1060,262 1150,290" fill="none" stroke="#94a3b8" stroke-width="4" '
        'stroke-linejoin="round"/>'
    )
    o.append(
        '<polyline points="790,490 1060,358 1150,330" fill="none" stroke="#94a3b8" stroke-width="4" '
        'stroke-linejoin="round"/>'
    )
    o.append(
        '<g><rect x="1112" y="244" width="76" height="26" rx="5" fill="#16a34a" filter="url(#lueur)">'
        '<animate attributeName="opacity" values=".35;1;.35" dur="1.8s" repeatCount="indefinite"/></rect>'
        '<rect x="1112" y="244" width="76" height="26" rx="5" fill="#15803d" stroke="#4ade80"/>'
        f'<text x="1150" y="262" text-anchor="middle" font-family="{POLICE}" font-size="13" '
        'font-weight="800" fill="#ffffff" letter-spacing="1.5">SORTIE</text></g>'
    )

    # Plage mouillee
    o.append('<rect x="500" y="150" width="290" height="340" fill="#0d2233"/>')
    o.append('<rect x="500" y="150" width="290" height="340" fill="url(#mouille)"/>')
    for cx, cy, rx, ry, d in [(585, 255, 46, 13, 3.2), (690, 395, 58, 15, 4.1), (720, 205, 32, 9, 2.7), (610, 455, 40, 10, 3.6)]:
        o.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#7dd3fc">'
            f'<animate attributeName="opacity" values=".06;.2;.06" dur="{d}s" repeatCount="indefinite"/></ellipse>'
        )
    # Panneau sol glissant
    o.append(
        '<g transform="translate(748 172)"><path d="M14 0 28 25H0Z" fill="#facc15" stroke="#0b1220" '
        'stroke-width="1.5" stroke-linejoin="round"/>'
        f'<text x="14" y="21.5" text-anchor="middle" font-family="{POLICE}" font-size="15" '
        'font-weight="900" fill="#0b1220">!</text></g>'
    )

    # Bassin
    o.append('<rect x="50" y="150" width="450" height="340" rx="18" fill="url(#eau)"/>')
    o.append('<g clip-path="url(#bassin)">')
    for y in (218, 286, 354, 422):
        o.append(
            f'<line x1="50" y1="{y}" x2="500" y2="{y}" stroke="#e0f2fe" stroke-opacity=".28" '
            'stroke-width="2" stroke-dasharray="6 10"/>'
        )
    for i, (y, d, op) in enumerate([(190, 7, 0.22), (300, 9, 0.16), (395, 8, 0.2), (460, 10, 0.14)]):
        vague = "M-60 {y} ".format(y=y) + " ".join(
            f"q 30 {-7 if k % 2 == 0 else 7} 60 0" for k in range(12)
        )
        sens = "-120" if i % 2 == 0 else "120"
        o.append(
            f'<path d="{vague}" fill="none" stroke="#bae6fd" stroke-opacity="{op}" stroke-width="2.5">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;{sens} 0" '
            f'dur="{d}s" repeatCount="indefinite"/></path>'
        )
    for i, (cx, cy) in enumerate([(130, 260), (260, 200), (380, 330), (170, 420), (330, 450), (440, 220), (220, 330)]):
        d = 2.4 + 0.37 * i
        o.append(
            f'<circle cx="{cx}" cy="{cy}" r="4" fill="none" stroke="#e0f2fe" stroke-width="1.6">'
            f'<animate attributeName="r" values="3;30" dur="{d:.2f}s" begin="-{0.5 * i:.1f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="stroke-opacity" values=".55;0" dur="{d:.2f}s" begin="-{0.5 * i:.1f}s" repeatCount="indefinite"/></circle>'
        )
    o.append("</g>")
    o.append('<rect x="50" y="150" width="450" height="340" rx="18" fill="none" stroke="#7dd3fc" stroke-width="4"/>')
    # Echelles
    for y0 in (203, 387):
        o.append(f'<g stroke="#e2e8f0" stroke-width="3" stroke-linecap="round">')
        o.append(f'<line x1="492" y1="{y0}" x2="492" y2="{y0 + 50}"/><line x1="508" y1="{y0}" x2="508" y2="{y0 + 50}"/>')
        for k in range(5):
            yy = y0 + 6 + k * 10
            o.append(f'<line x1="492" y1="{yy}" x2="508" y2="{yy}" stroke-width="2"/>')
        o.append("</g>")

    # Libelles de zones
    for x0, texte, coul in [(72, "BASSIN", "#bae6fd"), (522, "PLAGE MOUILLÉE", "#7dd3fc"), (812, "ZONE SÈCHE · GOULOT", "#cbd5e1")]:
        o.append(
            f'<text x="{x0}" y="180" font-family="{POLICE}" font-size="13" font-weight="700" '
            f'letter-spacing="2.2" fill="{coul}" fill-opacity=".85">{escape(texte)}</text>'
        )
    o.append(
        f'<text x="522" y="478" font-family="{POLICE}" font-size="12.5" fill="#7dd3fc" fill-opacity=".75">'
        "adhérence ↓ · inertie ↑</text>"
    )
    o.append(
        f'<text x="72" y="478" font-family="{POLICE}" font-size="12.5" fill="#e0f2fe" fill-opacity=".75">'
        "traînée visqueuse · extraction répartie</text>"
    )
    o.append(
        f'<text x="935" y="478" font-family="{POLICE}" font-size="12.5" fill="#cbd5e1" fill-opacity=".7">'
        "sortie unique · débit mesuré</text>"
    )

    # Agents
    o.append('<g filter="url(#halo)">')
    for d, kp, kt, dur, debut, coul in agents:
        kps = ";".join(f"{v:.4f}" for v in kp)
        kts = ";".join(f"{v:.4f}" for v in kt)
        o.append(
            f'<circle r="6.5" fill="{coul}" stroke="{FOND}" stroke-width="1.5" opacity="0">'
            f'<animateMotion path="{d}" dur="{dur:.2f}s" begin="{debut:.2f}s" repeatCount="indefinite" '
            f'calcMode="linear" keyPoints="{kps}" keyTimes="{kts}"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.03;.95;1" '
            f'dur="{dur:.2f}s" begin="{debut:.2f}s" repeatCount="indefinite"/></circle>'
        )
    o.append("</g>")
    o.append("</svg>")
    (SORTIE / "banniere.svg").write_text("\n".join(o), encoding="utf-8")


# --------------------------------------------------------------------------
# 2. Diagramme fondamental anime (Weidmann, constantes du projet)
# --------------------------------------------------------------------------

V0, GAMMA, RHO_MAX = 1.34, 1.913, 5.4


def weidmann(rho):
    return rho * V0 * (1 - math.exp(-GAMMA * (1 / rho - 1 / RHO_MAX)))


def diagramme():
    L, H = 1200, 520
    x0, x1, y0, y1 = 120, 1120, 440, 92
    rho_lim, j_lim = 5.6, 1.6

    def px(rho):
        return x0 + rho / rho_lim * (x1 - x0)

    def py(j):
        return y0 - j / j_lim * (y0 - y1)

    rhos = [0.02 + i * (RHO_MAX - 0.02) / 400 for i in range(401)]
    js = [weidmann(r) for r in rhos]
    k_max = max(range(len(js)), key=js.__getitem__)
    rho_e, j_e = rhos[k_max], js[k_max]

    def lisse(r):
        s = min(max((r - rho_e) / 1.2, 0.0), 1.0)
        return s * s * (3 - 2 * s)

    def trace(fn):
        pts = [(px(r), py(fn(r))) for r in rhos]
        return "M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in pts)

    d_w = trace(weidmann)
    d_t = trace(lambda r: weidmann(r) * (1 + 0.22 * lisse(r)))
    d_i = trace(lambda r: weidmann(r) * (1 - 0.3 * lisse(r)))

    o = []
    o.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L} {H}" width="{L}" height="{H}" '
        'role="img" aria-label="Diagramme fondamental : debit specifique en fonction de la densite, '
        'courbe de Weidmann et deux hypotheses a departager.">'
    )
    o.append(f'<rect width="{L}" height="{H}" rx="22" fill="{FOND}"/>')
    o.append(
        f'<text x="48" y="52" font-family="{POLICE}" font-size="25" font-weight="800" fill="#f1f5f9">'
        "Le diagramme fondamental, notre cible</text>"
    )
    o.append(
        f'<text x="48" y="78" font-family="{POLICE}" font-size="15" fill="#94a3b8">'
        "Combien de personnes franchissent le goulot, selon la densité de la foule ?</text>"
    )
    # Bande de la litterature
    o.append(
        f'<rect x="{x0}" y="{py(1.4):.1f}" width="{x1 - x0}" height="{py(1.2) - py(1.4):.1f}" '
        'fill="#facc15" fill-opacity=".08"/>'
    )
    o.append(
        f'<text x="{x0 + 10}" y="{py(1.4) - 7:.1f}" font-family="{POLICE}" '
        'font-size="13" fill="#fde68a" fill-opacity=".85">goulot, littérature : 1,2 – 1,4 pers/m/s</text>'
    )
    # Grille et axes
    for r in range(0, 6):
        o.append(f'<line x1="{px(r):.1f}" y1="{y0}" x2="{px(r):.1f}" y2="{y1}" stroke="#ffffff" stroke-opacity=".06"/>')
        o.append(
            f'<text x="{px(r):.1f}" y="{y0 + 24}" text-anchor="middle" font-family="{POLICE}" '
            f'font-size="14" fill="#94a3b8">{r}</text>'
        )
    for k in range(0, 5):
        j = 0.4 * k
        o.append(f'<line x1="{x0}" y1="{py(j):.1f}" x2="{x1}" y2="{py(j):.1f}" stroke="#ffffff" stroke-opacity=".06"/>')
        etiquette = f"{j:.1f}".replace(".", ",")
        o.append(
            f'<text x="{x0 - 14}" y="{py(j) + 5:.1f}" text-anchor="end" font-family="{POLICE}" '
            f'font-size="14" fill="#94a3b8">{etiquette}</text>'
        )
    o.append(f'<line x1="{x0}" y1="{y0}" x2="{x1 + 18}" y2="{y0}" stroke="#cbd5e1" stroke-width="2"/>')
    o.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1 - 18}" stroke="#cbd5e1" stroke-width="2"/>')
    o.append(
        f'<text x="{(x0 + x1) / 2:.0f}" y="{y0 + 54}" text-anchor="middle" font-family="{POLICE}" '
        'font-size="15" fill="#e2e8f0">densité ρ (pers/m²)</text>'
    )
    o.append(
        f'<text transform="translate({x0 - 62} {(y0 + y1) / 2:.0f}) rotate(-90)" text-anchor="middle" '
        f'font-family="{POLICE}" font-size="15" fill="#e2e8f0">débit spécifique J (pers/m/s)</text>'
    )

    cycle = "12s"
    # Hypotheses (apparaissent apres la courbe)
    for d, coul, etiq, pos in [
        (d_t, "#4ade80", "tampon : arrivées désynchronisées, débit ↑", (640, None, -18)),
        (d_i, "#fb923c", "inertielle : glissades et chocs, débit ↓", (560, 382, 0)),
    ]:
        o.append(
            f'<path d="{d}" fill="none" stroke="{coul}" stroke-width="3" stroke-dasharray="9 8" opacity="0">'
            f'<animate attributeName="opacity" values="0;0;.95;.95;0" keyTimes="0;.34;.44;.93;1" dur="{cycle}" repeatCount="indefinite"/></path>'
        )
        lab_x, lab_y, dy = pos
        if lab_y is None:
            r_lab = (lab_x - x0) / (x1 - x0) * rho_lim
            lab_y = py(weidmann(r_lab) * (1 + 0.22 * lisse(r_lab))) + dy
        o.append(
            f'<text x="{lab_x}" y="{lab_y:.1f}" font-family="{POLICE}" font-size="14" font-weight="600" '
            f'fill="{coul}" opacity="0">{escape(etiq)}'
            f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;.4;.5;.93;1" dur="{cycle}" repeatCount="indefinite"/></text>'
        )
    # Courbe de Weidmann tracee progressivement
    o.append(
        f'<path d="{d_w}" fill="none" stroke="#38bdf8" stroke-width="4.5" stroke-linecap="round" '
        'pathLength="1000" stroke-dasharray="1000" stroke-dashoffset="1000">'
        f'<animate attributeName="stroke-dashoffset" values="1000;0;0;0" keyTimes="0;.3;.93;1" dur="{cycle}" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="1;1;1;0" keyTimes="0;.3;.93;1" dur="{cycle}" repeatCount="indefinite"/></path>'
    )
    o.append(
        f'<circle r="8" fill="#e0f2fe" stroke="#38bdf8" stroke-width="3">'
        f'<animateMotion path="{d_w}" dur="{cycle}" repeatCount="indefinite" calcMode="linear" keyPoints="0;1;1" keyTimes="0;.3;1"/>'
        f'<animate attributeName="opacity" values="1;1;1;0" keyTimes="0;.3;.93;1" dur="{cycle}" repeatCount="indefinite"/></circle>'
    )
    # Maximum
    etiq_max = f"max ≈ {j_e:.2f} pers/m/s à ρ ≈ {rho_e:.1f} pers/m²".replace(".", ",")
    o.append(
        f'<g opacity="0"><line x1="{px(rho_e):.1f}" y1="{py(j_e):.1f}" x2="{px(rho_e):.1f}" y2="{y0}" '
        'stroke="#38bdf8" stroke-opacity=".5" stroke-dasharray="4 6"/>'
        f'<text x="{px(rho_e) - 60:.1f}" y="{py(j_e) - 16:.1f}" font-family="{POLICE}" font-size="14" fill="#7dd3fc">'
        f"{etiq_max}</text>"
        f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;.28;.33;.93;1" dur="{cycle}" repeatCount="indefinite"/></g>'
    )
    # Legende
    lx, ly = 250, 345
    for i, (coul, txt, tiret) in enumerate([
        ("#38bdf8", "Weidmann (1993), marche unidirectionnelle", ""),
        ("#4ade80", "hypothèse tampon (illustrative)", "9 8"),
        ("#fb923c", "hypothèse inertielle (illustrative)", "9 8"),
    ]):
        yy = ly + i * 24
        att = f' stroke-dasharray="{tiret}"' if tiret else ""
        o.append(f'<line x1="{lx}" y1="{yy}" x2="{lx + 34}" y2="{yy}" stroke="{coul}" stroke-width="3.5"{att}/>')
        o.append(f'<text x="{lx + 44}" y="{yy + 5}" font-family="{POLICE}" font-size="13.5" fill="#cbd5e1">{escape(txt)}</text>')
    o.append("</svg>")
    (SORTIE / "diagramme-fondamental.svg").write_text("\n".join(o), encoding="utf-8")
    return rho_e, j_e


# --------------------------------------------------------------------------
# 3. Terminal : sortie reelle de `viscocrowd valider-moteur` (extrait reformate)
# --------------------------------------------------------------------------


def terminal():
    lignes = [
        ("cmd", "$ viscocrowd valider-moteur"),
        ("titre", "Validation du moteur — bille dans une boîte en rotation"),
        ("sec", "1. Respect de la contrainte de confinement"),
        ("val", "   Δt = 1e-1 s    violation max   3.331e-16 m"),
        ("val", "   Δt = 1e-2 s    violation max   3.331e-16 m"),
        ("val", "   Δt = 1e-3 s    violation max   3.331e-16 m"),
        ("sec", "2. Énergie mécanique, boîte fixe"),
        ("val", "   dissipation totale    14.224500 J"),
        ("val", "   plus forte remontée   0.000e+00 J    (doit être ≤ 0)"),
        ("sec", "3. Entraînement solide : seulement si ω²R/g ≳ 1"),
        ("val", "   ω = 1 rad/s    écart 1.858e+00 m/s    régime gravitaire"),
        ("val", "   ω = 5 rad/s    écart 1.679e-02 m/s    régime centrifuge"),
        ("sec", "4. Exclusion entre agents, 36 disques, tolérance 1e-6 m"),
        ("val", "   Δt = 4e-3 s    recouvrement 1.00e-06 m    paroi 0.0 m    0/750"),
        ("val", "   Δt = 2e-3 s    recouvrement 1.00e-06 m    paroi 0.0 m    0/1500"),
        ("ok", "✔ Validation réussie : tous les critères chiffrés tiennent leur seuil."),
    ]
    couleurs = {"cmd": "#4ade80", "titre": "#f1f5f9", "sec": "#7dd3fc", "val": "#cbd5e1", "ok": "#4ade80"}
    L, pas, haut = 1200, 29, 86
    H = haut + pas * len(lignes) + 40
    cycle = 18.0
    o = []
    o.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L} {H}" width="{L}" height="{H}" role="img" '
        'aria-label="Terminal : sortie de la commande viscocrowd valider-moteur, tous les criteres tiennent leur seuil." xml:space="preserve">'
    )
    o.append(f'<rect width="{L}" height="{H}" rx="18" fill="#0a0f1a" stroke="#1e293b" stroke-width="2"/>')
    o.append(f'<path d="M0 18a18 18 0 0 1 18-18h{L - 36}a18 18 0 0 1 18 18v28H0z" fill="#111827"/>')
    for i, c in enumerate(["#ef4444", "#f59e0b", "#22c55e"]):
        o.append(f'<circle cx="{30 + 24 * i}" cy="23" r="7" fill="{c}"/>')
    o.append(
        f'<text x="{L / 2:.0f}" y="28" text-anchor="middle" font-family="{MONO}" font-size="14" fill="#64748b">'
        "ViscoCrowd-simulation — make valider</text>"
    )
    for i, (genre, txt) in enumerate(lignes):
        y = haut + i * pas
        t = 0.6 + i * 0.62 if i else 0.2
        fr = t / cycle
        poids = ' font-weight="700"' if genre in ("cmd", "sec", "ok", "titre") else ""
        o.append(
            f'<text x="34" y="{y}" font-family="{MONO}" font-size="17" fill="{couleurs[genre]}"{poids} opacity="0" xml:space="preserve" style="white-space:pre">{escape(txt)}'
            f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{fr:.4f};{fr + 0.012:.4f};.95;1" '
            f'dur="{cycle:.0f}s" repeatCount="indefinite"/></text>'
        )
    y_fin = haut + len(lignes) * pas
    t_fin = (0.6 + (len(lignes) - 1) * 0.62) / cycle
    o.append(
        f'<rect x="34" y="{y_fin - 17}" width="11" height="21" fill="#4ade80" opacity="0">'
        f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{t_fin:.4f};{t_fin + 0.01:.4f};.95;1" dur="{cycle:.0f}s" repeatCount="indefinite"/>'
        "</rect>"
    )
    o.append(
        f'<rect x="34" y="{y_fin - 17}" width="11" height="21" fill="#0a0f1a">'
        '<animate attributeName="opacity" values="0;1" dur="1s" calcMode="discrete" repeatCount="indefinite"/></rect>'
    )
    o.append("</svg>")
    (SORTIE / "terminal-validation.svg").write_text("\n".join(o), encoding="utf-8")


# --------------------------------------------------------------------------
# 4. Feuille de route des jalons
# --------------------------------------------------------------------------


def feuille_de_route():
    L, H = 1200, 330
    y = 168
    jalons = [
        ("J0", "Socle", "S1", "fait"),
        ("J1", "Moteur", "S2–S3", "fait"),
        ("J2", "Exclusion", "S4–S5", "fait"),
        ("J3", "Guidage + milieux", "S6–S7", "prochain"),
        ("J4", "Scénario piscine", "S8–S9", ""),
        ("J5", "Campagnes", "S10–S11", ""),
        ("J6", "Rapport", "S12–S13", ""),
    ]
    xs = [80 + i * 152 for i in range(len(jalons))]
    o = []
    o.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L} {H}" width="{L}" height="{H}" role="img" '
        'aria-label="Feuille de route : jalons 0 a 2 termines, jalon 3 a venir, rendu le 5 janvier 2027.">'
    )
    o.append(
        '<defs><linearGradient id="fait" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#0ea5e9"/>'
        '<stop offset="1" stop-color="#22d3ee"/></linearGradient>'
        '<filter id="lueur2" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4"/></filter></defs>'
    )
    o.append(f'<rect width="{L}" height="{H}" rx="22" fill="{FOND}"/>')
    o.append(
        f'<text x="48" y="54" font-family="{POLICE}" font-size="25" font-weight="800" fill="#f1f5f9">Où on en est</text>'
    )
    o.append(
        f'<text x="48" y="80" font-family="{POLICE}" font-size="15" fill="#94a3b8">'
        "13 semaines, 6 jalons, un rendu le 5 janvier 2027.</text>"
    )
    o.append(f'<line x1="{xs[0]}" y1="{y}" x2="1148" y2="{y}" stroke="#1e293b" stroke-width="8" stroke-linecap="round"/>')
    fin_fait = xs[2]
    o.append(
        f'<line x1="{xs[0]}" y1="{y}" x2="{xs[0]}" y2="{y}" stroke="url(#fait)" stroke-width="8" stroke-linecap="round">'
        f'<animate attributeName="x2" values="{xs[0]};{fin_fait};{fin_fait}" keyTimes="0;.3;1" dur="6s" fill="freeze" repeatCount="1"/>'
        f'<set attributeName="x2" to="{fin_fait}" begin="6s" fill="freeze"/></line>'
    )
    o.append(
        f'<circle r="6" cy="{y}" fill="#e0f2fe" filter="url(#lueur2)">'
        f'<animate attributeName="cx" values="{xs[0]};{fin_fait}" dur="2.4s" repeatCount="indefinite"/></circle>'
    )
    for (code, nom, sem, etat), x in zip(jalons, xs):
        if etat == "fait":
            o.append(f'<circle cx="{x}" cy="{y}" r="19" fill="url(#fait)"/>')
            o.append(
                f'<path d="M{x - 8} {y} l5.5 6 l10 -12" fill="none" stroke="{FOND}" stroke-width="3.5" '
                'stroke-linecap="round" stroke-linejoin="round"/>'
            )
        elif etat == "prochain":
            o.append(
                f'<circle cx="{x}" cy="{y}" r="19" fill="none" stroke="#facc15" stroke-width="3">'
                '<animate attributeName="r" values="19;30;19" dur="2s" repeatCount="indefinite"/>'
                '<animate attributeName="stroke-opacity" values=".9;0;.9" dur="2s" repeatCount="indefinite"/></circle>'
            )
            o.append(f'<circle cx="{x}" cy="{y}" r="17" fill="{FOND}" stroke="#facc15" stroke-width="3"/>')
        else:
            o.append(f'<circle cx="{x}" cy="{y}" r="17" fill="{FOND}" stroke="#334155" stroke-width="3"/>')
        coul = "#22d3ee" if etat == "fait" else ("#facc15" if etat == "prochain" else "#64748b")
        if etat != "fait":
            o.append(
                f'<text x="{x}" y="{y + 5}" text-anchor="middle" font-family="{POLICE}" font-size="13" '
                f'font-weight="800" fill="{coul}">{code}</text>'
            )
        o.append(
            f'<text x="{x}" y="{y + 50}" text-anchor="middle" font-family="{POLICE}" font-size="15" '
            f'font-weight="700" fill="{"#f1f5f9" if etat else "#94a3b8"}">{escape(code + " · " + nom if etat == "fait" else nom)}</text>'
        )
        o.append(
            f'<text x="{x}" y="{y + 72}" text-anchor="middle" font-family="{POLICE}" font-size="13" fill="#64748b">{sem}</text>'
        )
    # Bulle sur J2
    bx = xs[2]
    o.append(
        f'<g><rect x="{bx - 118}" y="{y - 74}" width="236" height="34" rx="17" fill="#082f49" stroke="#0ea5e9"/>'
        f'<text x="{bx}" y="{y - 52}" text-anchor="middle" font-family="{POLICE}" font-size="13.5" fill="#bae6fd">'
        "J2 livré en S2 · prévu S4–S5</text>"
        f'<path d="M{bx - 7} {y - 40} l7 9 l7 -9z" fill="#0ea5e9"/></g>'
    )
    # Echeance du rendu, au bout de la frise
    o.append(f'<circle cx="1148" cy="{y}" r="9" fill="#fb7185"/>')
    o.append(
        f'<g><rect x="1028" y="{y - 74}" width="134" height="34" rx="17" fill="#3f0d1d" stroke="#fb7185"/>'
        f'<text x="1095" y="{y - 52}" text-anchor="middle" font-family="{POLICE}" font-size="13.5" fill="#fecdd3">'
        "rendu · 5 janv.</text>"
        f'<path d="M1141 {y - 40} l7 9 l7 -9z" fill="#fb7185"/></g>'
    )
    o.append(
        f'<text x="1152" y="{y + 108}" text-anchor="end" font-family="{POLICE}" font-size="13" fill="#f9a8d4">'
        "soutenance · 19 janv. 2027</text>"
    )
    o.append("</svg>")
    (SORTIE / "feuille-de-route.svg").write_text("\n".join(o), encoding="utf-8")


banniere()
rho_e, j_e = diagramme()
terminal()
feuille_de_route()
print(f"Weidmann : maximum {j_e:.3f} pers/m/s a rho = {rho_e:.2f} pers/m2")
for p in sorted(SORTIE.glob("*.svg")):
    print(p.name, p.stat().st_size, "octets")
