"""Genere le logo anime de l'organisation ViscoCrowd.

Un mot-symbole qui se construit sous les yeux, en quatre temps :

  1. les mathematiques s'ecrivent en fond (courbes calculees, pas dessinees) ;
  2. les lettres tombent une a une, avec un rebond ;
  3. l'eau monte et les REMPLIT, par decoupe sur une surface ondulante ;
  4. la houle et les gouttes s'installent, puis la boucle repart.

Deux contraintes ont dicte la technique, l'une et l'autre apprises a la
lecture du logo precedent, un PNG sur fond blanc :

  - **Rien d'opaque et de clair en fond.** Un PNG a fond blanc affiche un pave
    blanc en theme sombre. On dessine donc un panneau sombre assume, arrondi,
    qui rend pareil dans les deux themes.
  - **Aucune dependance a une police.** GitHub sert les SVG via un proxy : une
    police web ne se charge pas, et la police systeme substituee change la
    largeur du texte, donc toute la mise en page. Chaque lettre porte donc un
    `textLength` qui FORCE sa largeur : la composition est identique partout,
    quelle que soit la police reellement utilisee.

Comme le reste du profil : bibliotheque standard seule, et tout ce qui est
trace est calcule.

Usage : python scripts/gen_logo.py profile/assets
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape

SORTIE = Path(sys.argv[1] if len(sys.argv) > 1 else "profile/assets")
SORTIE.mkdir(parents=True, exist_ok=True)

L, H = 1000, 340
DUREE = 9.0  # s, duree de la boucle complete

POLICE = "ui-sans-serif, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'Cascadia Code', Consolas, Menlo, monospace"

# Constantes de Weidmann, reprises du depot de simulation : la courbe du fond
# est la vraie courbe de reference du projet, pas une decoration.
V0, GAMMA, RHO_MAX = 1.34, 1.913, 5.4


def f(v: float) -> str:
    """Nombre court : les SVG animes pesent vite, et le profil a un budget."""
    return f"{v:.1f}".rstrip("0").rstrip(".")


def t(fraction: float) -> str:
    """Instant de la boucle, en fraction de DUREE, pour les keyTimes."""
    return f"{fraction:.4f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------------------
# Les mathematiques du fond, calculees
# ---------------------------------------------------------------------------


def courbe_weidmann(x0, y0, larg, haut, n=80):
    """Debit specifique J = rho * v(rho) de Weidmann, echantillonne."""
    pts = []
    for i in range(n + 1):
        rho = 0.02 + (RHO_MAX - 0.02) * i / n
        v = V0 * (1.0 - math.exp(-GAMMA * (1.0 / rho - 1.0 / RHO_MAX)))
        j = rho * max(v, 0.0)
        pts.append((x0 + larg * rho / RHO_MAX, y0 + haut * (1.0 - j / 1.3)))
    return pts


def onde_amortie(x0, y0, larg, amp, k, tau, n=90):
    """Onde stationnaire amortie : A e^{-x/tau} sin(k x). Solution type du bassin."""
    pts = []
    for i in range(n + 1):
        u = i / n
        x = u * larg
        pts.append((x0 + x, y0 - amp * math.exp(-x / tau) * math.sin(k * x)))
    return pts


def gaussienne(x0, y0, larg, haut, sigma=0.22, n=70):
    """Densite de la foule au goulot : un pic, pas un plateau."""
    pts = []
    for i in range(n + 1):
        u = i / n
        y = math.exp(-((u - 0.5) ** 2) / (2 * sigma * sigma))
        pts.append((x0 + larg * u, y0 + haut * (1.0 - y)))
    return pts


def polyligne(pts) -> str:
    return "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts)


def longueur_polyligne(pts) -> float:
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:], strict=False))


def trace_qui_s_ecrit(pts, couleur, opacite, epaisseur, debut, duree_trace):
    """Chemin revele par deroulement du trait : l'effet « on l'ecrit »."""
    d = polyligne(pts)
    lg = longueur_polyligne(pts) + 2
    fin = debut + duree_trace
    return (
        f'<path d="{d}" fill="none" stroke="{couleur}" stroke-opacity="{opacite}" '
        f'stroke-width="{epaisseur}" stroke-linecap="round" stroke-linejoin="round" '
        f'stroke-dasharray="{f(lg)}" stroke-dashoffset="{f(lg)}">'
        f'<animate attributeName="stroke-dashoffset" dur="{f(DUREE)}s" repeatCount="indefinite" '
        f'values="{f(lg)};{f(lg)};0;0;{f(lg)}" '
        f'keyTimes="0;{t(debut)};{t(fin)};{t(0.9)};1" '
        f'calcMode="spline" keySplines=".4 0 .6 1;.2 .6 .2 1;0 0 1 1;.4 0 .6 1"/>'
        f"</path>"
    )


# ---------------------------------------------------------------------------
# Le mot-symbole
# ---------------------------------------------------------------------------

# Largeur relative de chaque glyphe. Elle n'a pas besoin d'etre exacte : le
# `textLength` la rend vraie. Elle sert seulement a ce que les lettres gardent
# des proportions credibles avant d'etre forcees.
LARGEURS = {
    "V": 0.74,
    "i": 0.28,
    "s": 0.54,
    "c": 0.57,
    "o": 0.64,
    "C": 0.78,
    "r": 0.44,
    "w": 0.92,
    "d": 0.66,
}

MOT = "ViscoCrowd"
COUPURE = 5  # « Visco » puis « Crowd », deux teintes comme dans le mot lui-meme


def disposer(mot, x_debut, largeur_totale):
    """Position et largeur imposee de chaque lettre."""
    poids = [LARGEURS[c] for c in mot]
    unite = largeur_totale / sum(poids)
    lettres, x = [], x_debut
    for c, p in zip(mot, poids, strict=True):
        lettres.append((c, x, p * unite))
        x += p * unite
    return lettres


def lettre(c, x, larg, base, taille, retard):
    """Une lettre de bande dessinee : contour epais, chute avec rebond.

    `paint-order="stroke"` dessine le contour SOUS le remplissage : le trait ne
    mange pas la lettre, il l'entoure. C'est ce qui donne le trait de BD.
    """
    commun = (
        f'x="{f(x)}" y="{f(base)}" textLength="{f(larg)}" lengthAdjust="spacingAndGlyphs" '
        f'font-family="{POLICE}" font-size="{f(taille)}" font-weight="900" '
        f'font-style="italic" letter-spacing="0"'
    )
    atterrissage = retard + 0.085
    rebond = atterrissage + 0.035
    pose = rebond + 0.03
    anim = (
        f'<animateTransform attributeName="transform" type="translate" '
        f'dur="{f(DUREE)}s" repeatCount="indefinite" additive="sum" '
        f'values="0 -260;0 -260;0 14;0 -7;0 0;0 0;0 -260" '
        f'keyTimes="0;{t(retard)};{t(atterrissage)};{t(rebond)};{t(pose)};{t(0.93)};1" '
        f'calcMode="spline" '
        f'keySplines="0 0 1 1;.5 .05 .6 1;.3 0 .7 1;.3 0 .7 1;0 0 1 1;.5 0 .7 1"/>'
        f'<animate attributeName="opacity" dur="{f(DUREE)}s" repeatCount="indefinite" '
        f'values="0;0;1;1;0" keyTimes="0;{t(retard)};{t(atterrissage)};{t(0.93)};1"/>'
    )
    glyphe = escape(c)
    return (
        f"<g>"
        # Ombre portee, decalee : l'epaisseur de la BD.
        f'<text {commun} fill="#082036" opacity=".85" transform="translate(7 9)">{glyphe}</text>'
        # Contour puis remplissage.
        f'<text {commun} fill="url(#vide)" stroke="#061625" stroke-width="13" '
        f'paint-order="stroke" stroke-linejoin="round">{glyphe}</text>'
        f"{anim}</g>"
    )


def lettres_pour_decoupe(lettres, base, taille):
    """Les memes lettres, pleines, revelees par la montee de l'eau.

    C'est ce calque qui porte la couleur du mot : au repos les lettres sont
    sombres, « vides », et c'est l'eau qui les allume en montant. Sans ce
    contraste le remplissage ne se verrait pas, les deux etats etant bleus.
    """
    out = []
    for i, (c, x, larg) in enumerate(lettres):
        teinte = "url(#visco)" if i < COUPURE else "url(#crowd)"
        out.append(
            f'<text x="{f(x)}" y="{f(base)}" textLength="{f(larg)}" '
            f'lengthAdjust="spacingAndGlyphs" font-family="{POLICE}" '
            f'font-size="{f(taille)}" font-weight="900" font-style="italic" '
            f'fill="{teinte}">{escape(c)}</text>'
        )
    return "".join(out)


def vague(y, amplitude, longueur_onde, phase, largeur, profondeur):
    """Surface sinusoidale fermee vers le bas : sert de decoupe et de houle."""
    pts = []
    n = 72
    for i in range(n + 1):
        x = largeur * i / n
        pts.append((x, y + amplitude * math.sin(2 * math.pi * x / longueur_onde + phase)))
    d = polyligne(pts)
    return f"{d} L{f(largeur)} {f(profondeur)} L0 {f(profondeur)} Z"


# ---------------------------------------------------------------------------
# Assemblage
# ---------------------------------------------------------------------------


def logo() -> str:
    base, taille = 214.0, 132.0
    lettres = disposer(MOT, 92.0, 820.0)

    o: list[str] = []
    o.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L} {H}" width="{L}" '
        f'height="{H}" role="img" aria-label="ViscoCrowd">'
    )
    o.append(
        "<title>ViscoCrowd</title>"
        "<desc>Logo anime : des courbes mathematiques s'ecrivent, les lettres de "
        "ViscoCrowd tombent une a une, puis l'eau monte et les remplit.</desc>"
    )

    # --- definitions ---------------------------------------------------------
    o.append("<defs>")
    o.append(
        '<linearGradient id="panneau" x1="0" y1="0" x2=".6" y2="1">'
        '<stop offset="0" stop-color="#0d1b2e"/>'
        '<stop offset=".55" stop-color="#0b1220"/>'
        '<stop offset="1" stop-color="#07131f"/></linearGradient>'
    )
    o.append(
        '<linearGradient id="visco" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#bae6fd"/>'
        '<stop offset=".5" stop-color="#38bdf8"/>'
        '<stop offset="1" stop-color="#0284c7"/></linearGradient>'
    )
    o.append(
        '<linearGradient id="crowd" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#a5f3fc"/>'
        '<stop offset=".5" stop-color="#22d3ee"/>'
        '<stop offset="1" stop-color="#0e7490"/></linearGradient>'
    )
    o.append(
        '<linearGradient id="vide" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#14344f"/>'
        '<stop offset="1" stop-color="#0a1d2e"/></linearGradient>'
    )
    o.append(
        '<linearGradient id="eau-lettres" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#e0f2fe" stop-opacity=".95"/>'
        '<stop offset="1" stop-color="#0ea5e9" stop-opacity=".9"/></linearGradient>'
    )
    o.append(
        '<linearGradient id="houle" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#38bdf8" stop-opacity=".55"/>'
        '<stop offset="1" stop-color="#0b4fb3" stop-opacity=".22"/></linearGradient>'
    )
    o.append(
        '<radialGradient id="halo" cx=".5" cy=".42" r=".62">'
        '<stop offset="0" stop-color="#1e5f8f" stop-opacity=".45"/>'
        '<stop offset="1" stop-color="#1e5f8f" stop-opacity="0"/></radialGradient>'
    )
    o.append(
        '<pattern id="grille" width="40" height="40" patternUnits="userSpaceOnUse">'
        '<path d="M40 0H0V40" fill="none" stroke="#7dd3fc" stroke-opacity=".07"/></pattern>'
    )

    # Decoupe : la surface de l'eau qui monte a travers les lettres.
    montee = (
        f'<animateTransform attributeName="transform" type="translate" '
        f'dur="{f(DUREE)}s" repeatCount="indefinite" '
        f'values="0 190;0 190;0 -58;0 -58;0 190" '
        f'keyTimes="0;{t(0.50)};{t(0.70)};{t(0.93)};1" '
        f'calcMode="spline" keySplines="0 0 1 1;.25 .1 .25 1;0 0 1 1;.5 0 .7 1"/>'
    )
    o.append('<clipPath id="niveau">')
    o.append(f'<path d="{vague(150, 9, 300, 0, L, H + 40)}">')
    o.append(montee)
    o.append(
        f'<animate attributeName="d" dur="5s" repeatCount="indefinite" '
        f'values="{vague(150, 9, 300, 0, L, H + 40)};'
        f"{vague(150, 9, 300, math.pi, L, H + 40)};"
        f'{vague(150, 9, 300, 2 * math.pi, L, H + 40)}"/>'
    )
    o.append("</path></clipPath>")
    o.append("</defs>")

    # --- fond ----------------------------------------------------------------
    o.append(f'<rect width="{L}" height="{H}" rx="26" fill="url(#panneau)"/>')
    o.append(f'<rect width="{L}" height="{H}" rx="26" fill="url(#grille)"/>')
    o.append(f'<rect width="{L}" height="{H}" rx="26" fill="url(#halo)"/>')

    # --- mathematiques qui s'ecrivent ---------------------------------------
    o.append(
        trace_qui_s_ecrit(
            courbe_weidmann(600, 48, 330, 150), "#7dd3fc", ".40", 2.6, 0.02, 0.14
        )
    )
    o.append(
        trace_qui_s_ecrit(
            onde_amortie(70, 286, 420, 26, 0.055, 190), "#38bdf8", ".34", 2.4, 0.05, 0.15
        )
    )
    o.append(
        trace_qui_s_ecrit(gaussienne(360, 40, 240, 92), "#22d3ee", ".26", 2.2, 0.08, 0.13)
    )

    equations = [
        (66, 60, 19, "∂u/∂t + (u·∇)u = −∇p/ρ + ν∇²u"),
        (66, 92, 17, "K = { X : |xᵢ − xⱼ| ≥ rᵢ + rⱼ }"),
        (700, 238, 17, "vⁿ⁺¹ = (xⁿ⁺¹ − xⁿ)/Δt"),
        (646, 44, 15, "J(ρ) = ρ · v(ρ)"),
    ]
    for i, (x, y, taille_eq, texte) in enumerate(equations):
        apparition = 0.10 + 0.035 * i
        o.append(
            f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{taille_eq}" '
            f'fill="#7dd3fc" fill-opacity=".52" opacity="0">{escape(texte)}'
            f'<animate attributeName="opacity" dur="{f(DUREE)}s" repeatCount="indefinite" '
            f'values="0;0;1;1;0" '
            f'keyTimes="0;{t(apparition)};{t(apparition + 0.05)};{t(0.92)};1"/>'
            f"</text>"
        )

    # --- lettres -------------------------------------------------------------
    o.append("<g>")
    for i, (c, x, larg) in enumerate(lettres):
        o.append(lettre(c, x, larg, base, taille, 0.20 + 0.020 * i))
    o.append("</g>")

    # --- l'eau remplit les lettres ------------------------------------------
    o.append(f'<g clip-path="url(#niveau)">{lettres_pour_decoupe(lettres, base, taille)}</g>')

    # --- houle de surface ----------------------------------------------------
    for k, (amp, lam, op, vitesse) in enumerate(
        ((11, 340, ".50", 7.0), (8, 230, ".34", 5.0), (6, 170, ".22", 9.0))
    ):
        o.append(f'<g opacity="0"><path d="{vague(252 + 7 * k, amp, lam, k, L, H + 40)}" ')
        o.append('fill="url(#houle)">')
        o.append(
            f'<animate attributeName="d" dur="{f(vitesse)}s" repeatCount="indefinite" '
            f'values="{vague(252 + 7 * k, amp, lam, k, L, H + 40)};'
            f"{vague(252 + 7 * k, amp, lam, k + math.pi, L, H + 40)};"
            f'{vague(252 + 7 * k, amp, lam, k + 2 * math.pi, L, H + 40)}"/>'
        )
        o.append("</path>")
        o.append(
            f'<animate attributeName="opacity" dur="{f(DUREE)}s" repeatCount="indefinite" '
            f'values="0;0;1;1;0" keyTimes="0;{t(0.52)};{t(0.68)};{t(0.93)};1"/>'
        )
        o.append("</g>")

    # --- gouttes : elles partent de l'impact de chaque lettre ----------------
    for i, (_, x, larg) in enumerate(lettres):
        for j, (dx, dy, r) in enumerate(((-22, -54, 4.5), (16, -70, 3.4), (34, -40, 2.8))):
            depart = 0.20 + 0.020 * i + 0.085
            o.append(
                f'<circle cx="{f(x + larg / 2 + dx)}" cy="{f(base - 24)}" r="{f(r)}" '
                f'fill="#bae6fd" opacity="0">'
                f'<animate attributeName="opacity" dur="{f(DUREE)}s" repeatCount="indefinite" '
                f'values="0;0;.9;0;0" '
                f'keyTimes="0;{t(depart)};{t(depart + 0.012)};{t(depart + 0.075)};1"/>'
                f'<animateTransform attributeName="transform" type="translate" '
                f'dur="{f(DUREE)}s" repeatCount="indefinite" '
                f'values="0 0;0 0;{f(dx * 0.7)} {f(dy)};{f(dx * 1.4)} 30;{f(dx * 1.4)} 30" '
                f'keyTimes="0;{t(depart)};{t(depart + 0.04)};{t(depart + 0.075)};1" '
                f'calcMode="spline" keySplines="0 0 1 1;.2 .7 .4 1;.5 0 .9 .6;0 0 1 1"/>'
                f"</circle>"
            )
            _ = j

    # --- signature -----------------------------------------------------------
    o.append(
        f'<text x="{L / 2}" y="296" text-anchor="middle" font-family="{POLICE}" '
        f'font-size="19" font-weight="600" fill="#7dd3fc" fill-opacity=".85" '
        f'letter-spacing="3.5" opacity="0">'
        f"{escape('évacuation d’une piscine en panique')}"
        f'<animate attributeName="opacity" dur="{f(DUREE)}s" repeatCount="indefinite" '
        f'values="0;0;1;1;0" keyTimes="0;{t(0.74)};{t(0.80)};{t(0.93)};1"/>'
        f"</text>"
    )

    o.append("</svg>")
    return "".join(o)


def main() -> None:
    chemin = SORTIE / "logo-viscocrowd.svg"
    chemin.write_text(logo(), encoding="utf-8")
    print(f"ok  {chemin}  {chemin.stat().st_size} octets")


if __name__ == "__main__":
    main()
