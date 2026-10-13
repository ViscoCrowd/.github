"""Animation ASCII (eau, foule, viscosite) et cartes d'equipe avec avatars embarques."""

import base64
import math
import random
import sys
from pathlib import Path
from xml.sax.saxutils import escape

SORTIE = Path(sys.argv[1])
AVATARS = Path(sys.argv[2])
POLICE = "ui-sans-serif, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'Cascadia Mono', Consolas, Menlo, monospace"
FOND = "#0b1220"

COLS, ROWS = 96, 18
TAILLE, LARG_CAR, INTERLIGNE = 14, 8.43, 18
X0 = (1200 - COLS * LARG_CAR) / 2
Y0 = 92
PAS = 0.15  # s par image


def grille():
    return [[" "] * COLS for _ in range(ROWS)]


# --------------------------------------------------------------------------
# Acte 1 : le bassin
# --------------------------------------------------------------------------


def acte_eau(n):
    images = []
    rng = random.Random(7)
    bulles = [(rng.randrange(4, COLS - 4), rng.uniform(0, 12), rng.uniform(0.35, 0.7)) for _ in range(14)]
    for t in range(n):
        g = grille()
        surf = [
            6 + 1.6 * math.sin(0.21 * c - 0.9 * t * 0.6) + 0.7 * math.sin(0.43 * c + 0.6 * t * 0.6)
            for c in range(COLS)
        ]
        for c in range(COLS):
            s = surf[c]
            for r in range(ROWS):
                if r < s - 0.5:
                    continue
                prof = r - s
                if prof < 0.5:
                    crete = c > 0 and c < COLS - 1 and s <= surf[c - 1] and s <= surf[c + 1]
                    g[r][c] = "^" if crete else "~"
                elif prof < 1.5:
                    g[r][c] = "≈"
                else:
                    # Courants lents : des filets qui derivent vers la droite.
                    h = (c * 7 + r * 13 - int(t * 0.8)) % 23
                    g[r][c] = "-" if h == 0 else ("~" if h == 11 and prof < 6 else " ")
        for bc, phase, v in bulles:
            r = ROWS - 1 - ((t * v + phase) % 11)
            r = int(round(r))
            if r > surf[bc] + 1 and 0 <= r < ROWS:
                g[r][bc] = "o" if (t + bc) % 3 else "°"
        # Un nageur traverse le bassin
        x = int(4 + t * 1.6) % (COLS - 6)
        rs = int(round(surf[x + 1])) - 1
        for k, ch in enumerate("\\o/" if t % 4 < 2 else "_o_"):
            if 0 <= rs < ROWS:
                g[rs][x + k] = ch
        images.append({"lignes": ["".join(l) for l in g]})
    return images


def couleur_eau(r):
    palette = ["#e0f2fe", "#e0f2fe", "#bae6fd", "#bae6fd", "#7dd3fc", "#7dd3fc", "#38bdf8", "#38bdf8",
               "#0ea5e9", "#0ea5e9", "#0284c7", "#0284c7", "#0369a1", "#0369a1", "#1d4ed8", "#1d4ed8",
               "#1e40af", "#1e3a8a"]
    return palette[r]


# --------------------------------------------------------------------------
# Acte 2 : la foule, un petit automate cellulaire vers une porte unique
# --------------------------------------------------------------------------

PORTE = (8, 10)  # rangees libres a la porte


def borne(c):
    if c < 50:
        return 0.5, ROWS - 1.5
    k = (min(c, 88) - 50) / 38
    return 0.5 + k * (PORTE[0] - 0.5 - 0.0), ROWS - 1.5 - k * (ROWS - 1.5 - PORTE[1])


def libre(c, r):
    if c < 0 or c >= COLS or r < 0 or r >= ROWS:
        return False
    if c >= 88:
        return PORTE[0] <= r <= PORTE[1]
    haut, bas = borne(c)
    return haut < r < bas


def acte_foule(n):
    rng = random.Random(42)
    agents = {}
    sortis = 0
    images = []
    mur = grille()
    for c in range(50, 89):
        haut, bas = borne(c)
        mur[int(math.floor(haut))][c] = "\\"
        mur[int(math.ceil(bas))][c] = "/"
    for c in range(0, 50):
        mur[0][c] = "_"
        mur[ROWS - 1][c] = "‾"
    for r in range(ROWS):
        if not (PORTE[0] <= r <= PORTE[1]):
            for c in (88, 89):
                if mur[r][c] == " ":
                    mur[r][c] = "|"
    decor = ["".join(l) for l in mur]

    for t in range(70 + n):
        # Arrivees continues par la gauche
        for _ in range(3):
            r = rng.randrange(2, ROWS - 2)
            if (0, r) not in agents and rng.random() < 0.55:
                agents[(0, r)] = False
        nouveaux = {}
        ordre = sorted(agents, key=lambda p: -p[0])  # les plus avances bougent d'abord
        for c, r in ordre:
            cible_r = 9
            dr = 0 if r == cible_r else (1 if r < cible_r else -1)
            essais = [(c + 1, r + dr), (c + 1, r), (c + 1, r - dr if dr else r + rng.choice((-1, 1))), (c, r + dr)]
            bouge = False
            for nc, nr in essais:
                if nc >= COLS:
                    sortis += 1
                    bouge = True
                    break
                if libre(nc, nr) and (nc, nr) not in nouveaux and (nc, nr) not in agents:
                    nouveaux[(nc, nr)] = False
                    bouge = True
                    break
            else:
                nouveaux[(c, r)] = True  # bloque : il pousse
            if bouge and nc >= COLS:
                continue
        agents = nouveaux
        if t >= 70:
            g = [list(l) for l in decor]
            for (c, r), bloque in agents.items():
                g[r][c] = "@" if bloque else "o"
            for c in range(90, COLS):
                for r in range(PORTE[0], PORTE[1] + 1):
                    if g[r][c] == " ":
                        g[r][c] = "›"
            images.append({"lignes": ["".join(l) for l in g], "compteur": sortis})
    return images, decor


# --------------------------------------------------------------------------
# Acte 3 : « VISCO » fond et goutte
# --------------------------------------------------------------------------

LETTRES = {
    "V": ["#   #", "#   #", "#   #", " # # ", "  #  "],
    "I": ["#####", "  #  ", "  #  ", "  #  ", "#####"],
    "S": [" ####", "#    ", " ### ", "    #", "#### "],
    "C": [" ####", "#    ", "#    ", "#    ", " ####"],
    "O": [" ### ", "#   #", "#   #", "#   #", " ### "],
}


def acte_visco(n):
    rng = random.Random(3)
    mot = "VISCO"
    largeur = len(mot) * 12 - 2
    x0 = (COLS - largeur) // 2
    pix = set()
    for i, ch in enumerate(mot):
        for r, ligne in enumerate(LETTRES[ch]):
            for c, v in enumerate(ligne):
                if v == "#":
                    for dy in (0, 1):
                        for dx in (0, 1):
                            pix.add((1 + 2 * r + dy, x0 + i * 12 + 2 * c + dx))
    bas = {}
    for r, c in pix:
        bas[c] = max(bas.get(c, -1), r)
    colonnes = [c for c in bas if rng.random() < 0.45]
    gouttes = {c: (rng.uniform(0, n * 0.45), rng.uniform(0.18, 0.5), rng.randint(2, 5)) for c in colonnes}
    flaque = [0.0] * COLS
    images = []
    lettres = grille()
    for r, c in pix:
        lettres[r][c] = "█"
    decor = ["".join(l) for l in lettres]
    for t in range(n):
        g = grille()
        for c, (t0, v, lmax) in gouttes.items():
            r0 = bas[c] + 1
            long_ = max(0.0, min(lmax, (t - t0) * v))
            for k in range(int(long_)):
                if r0 + k < ROWS - 1:
                    g[r0 + k][c] = "▓" if k == 0 else "|"
            if long_ >= lmax:
                tm = t0 + lmax / v
                chute = (t - tm) * 1.3
                rd = int(r0 + lmax + chute)
                if rd < ROWS - 1:
                    g[rd][c] = "o"
                else:
                    flaque[c] = min(flaque[c] + 0.35, 3.0)
        for c in range(COLS):
            niveau = flaque[c] + 0.5 * (flaque[c - 1] if c else 0) + 0.5 * (flaque[c + 1] if c < COLS - 1 else 0)
            if niveau > 0.4:
                g[ROWS - 1][c] = "≈" if niveau > 1.6 else "~"
        images.append({"lignes": ["".join(l) for l in g]})
    return images, decor


def ligne_texte(x, y, txt, coul, poids=""):
    # La police et le blanc preserve viennent de la classe `m` (feuille de style du SVG) :
    # les repeter sur des milliers de lignes triplait le poids du fichier.
    return f'<text class="m" x="{x:.1f}" y="{y:.1f}" fill="{coul}"{poids} xml:space="preserve">{escape(txt)}</text>'


def visible(debut, fin, total):
    """Animation d'opacite discrete : visible de l'image `debut` (incluse) a `fin` (exclue)."""
    a, b = debut / total, fin / total
    if debut == 0:
        vals, kts = "1;0", f"0;{b:.5f}"
    elif fin >= total:
        vals, kts = "0;1", f"0;{a:.5f}"
    else:
        vals, kts = "0;1;0", f"0;{a:.5f};{b:.5f}"
    return (
        f'<animate attributeName="opacity" values="{vals}" keyTimes="{kts}" calcMode="discrete" '
        f'dur="{total * PAS:.2f}s" repeatCount="indefinite"/>'
    )


def ascii_anim():
    eau = acte_eau(30)
    foule, decor_foule = acte_foule(46)
    visco, decor_visco = acte_visco(44)
    total = len(eau) + len(foule) + len(visco)
    H = Y0 + ROWS * INTERLIGNE + 66
    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 {H}" width="1200" height="{H}" role="img" '
        'aria-label="Animation ASCII en trois actes : un bassin, une foule qui se presse vers une porte, le mot VISCO qui fond.">'
    ]
    o.append(f"<style>.m{{font-family:{MONO};font-size:{TAILLE}px;white-space:pre}}</style>")
    o.append(f'<rect width="1200" height="{H}" rx="20" fill="#05080f" stroke="#1e293b" stroke-width="2"/>')
    o.append('<path d="M0 20a20 20 0 0 1 20-20h1160a20 20 0 0 1 20 20v26H0z" fill="#0d1424"/>')
    for i, c in enumerate(["#ef4444", "#f59e0b", "#22c55e"]):
        o.append(f'<circle cx="{30 + 24 * i}" cy="23" r="7" fill="{c}"/>')
    o.append(
        f'<text x="600" y="28" text-anchor="middle" font-family="{MONO}" font-size="14" fill="#64748b">'
        "viscocrowd — eau · foule · viscosité</text>"
    )
    # Indicateur d'acte
    actes = [("1 · eau", 0, len(eau), "#38bdf8"), ("2 · foule", len(eau), len(eau) + len(foule), "#f1f5f9"),
             ("3 · visco", len(eau) + len(foule), total, "#f59e0b")]
    for i, (nom, a, b, coul) in enumerate(actes):
        x = 905 + i * 92
        o.append(f'<rect x="{x}" y="58" width="84" height="22" rx="11" fill="#0f172a" stroke="#1e293b"/>')
        o.append(f'<rect x="{x}" y="58" width="84" height="22" rx="11" fill="{coul}" fill-opacity=".18" stroke="{coul}" opacity="0">{visible(a, b, total)}</rect>')
        o.append(f'<text x="{x + 42}" y="73" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{coul}">{nom}</text>')

    def bloc(images, debut, couleurs, poids=""):
        for k, img in enumerate(images):
            o.append(f'<g opacity="{1 if debut + k == 0 else 0}">{visible(debut + k, debut + k + 1, total)}')
            for r, txt in enumerate(img["lignes"]):
                if txt.strip():
                    o.append(ligne_texte(X0, Y0 + r * INTERLIGNE, txt, couleurs(r), poids))
            o.append("</g>")

    bloc(eau, 0, couleur_eau)
    # Foule : decor statique pendant l'acte, agents image par image
    d0 = len(eau)
    o.append(f'<g opacity="0">{visible(d0, d0 + len(foule), total)}')
    for r, txt in enumerate(decor_foule):
        if txt.strip():
            o.append(ligne_texte(X0, Y0 + r * INTERLIGNE, txt, "#64748b"))
    o.append(
        f'<text x="{X0 + 90 * LARG_CAR:.1f}" y="{Y0 + 6.6 * INTERLIGNE:.1f}" font-family="{MONO}" font-size="12" '
        'font-weight="700" fill="#22c55e">EXIT</text></g>'
    )
    for k, img in enumerate(foule):
        o.append(f'<g opacity="0">{visible(d0 + k, d0 + k + 1, total)}')
        for r, txt in enumerate(img["lignes"]):
            agents_seuls = "".join(ch if ch in "o@›" else " " for ch in txt)
            if agents_seuls.strip():
                pousse = "".join(ch if ch == "@" else " " for ch in agents_seuls)
                marche = "".join(ch if ch == "o" else " " for ch in agents_seuls)
                sortie = "".join(ch if ch == "›" else " " for ch in agents_seuls)
                if marche.strip():
                    o.append(ligne_texte(X0, Y0 + r * INTERLIGNE, marche, "#f8fafc", ' font-weight="700"'))
                if pousse.strip():
                    o.append(ligne_texte(X0, Y0 + r * INTERLIGNE, pousse, "#fb923c", ' font-weight="700"'))
                if sortie.strip():
                    o.append(ligne_texte(X0, Y0 + r * INTERLIGNE, sortie, "#22c55e"))
        o.append(
            f'<text x="{X0:.1f}" y="{Y0 + ROWS * INTERLIGNE + 22:.1f}" font-family="{MONO}" font-size="14" fill="#94a3b8" xml:space="preserve">'
            f'FOULE  ·  o marche   <tspan fill="#fb923c">@ bloqué, pousse</tspan>   ·  évacués : <tspan fill="#22c55e" font-weight="700">{img["compteur"] - foule[0]["compteur"]}</tspan></text>'
        )
        o.append("</g>")
    # Visco : lettres statiques, gouttes image par image
    v0 = len(eau) + len(foule)
    o.append(f'<g opacity="0">{visible(v0, total, total)}')
    for r, txt in enumerate(decor_visco):
        if txt.strip():
            o.append(ligne_texte(X0, Y0 + r * INTERLIGNE, txt, "#f59e0b"))
    o.append(
        f'<text x="{X0:.1f}" y="{Y0 + ROWS * INTERLIGNE + 22:.1f}" font-family="{MONO}" font-size="14" fill="#fbbf24">'
        "VISCO  ·  ça colle, ça freine, ça glisse</text></g>"
    )
    bloc(visco, v0, lambda r: "#fcd34d" if r < ROWS - 1 else "#d97706")
    # Legende de l'acte 1
    o.append(
        f'<g opacity="1">{visible(0, len(eau), total)}<text x="{X0:.1f}" y="{Y0 + ROWS * INTERLIGNE + 22:.1f}" '
        f'font-family="{MONO}" font-size="14" fill="#7dd3fc">BASSIN  ·  traînée visqueuse, on avance lentement</text></g>'
    )
    o.append("</svg>")
    (SORTIE / "ascii-eau-foule-visco.svg").write_text("\n".join(o), encoding="utf-8")
    return total


# --------------------------------------------------------------------------
# Cartes d'equipe
# --------------------------------------------------------------------------

EQUIPE = [
    ("CodeByHaamza", "Hamza Karrouchi", "Moteur & exclusion", "#38bdf8", "#0ea5e9",
     ["socle et moteur validé (#1)", "projection d’exclusion (#6)", "intégration continue (#5)"]),
    ("shalee-pnt", "Shaleena Lesueur", "Observables & spécification", "#f472b6", "#db2777",
     ["débit à travers une ligne (#9)", "référence de Weidmann (#9)", "spécification § 2.5 (#7)"]),
    ("lennymgrd", "Lenny Mongrandi", "Interface, planning & relecture", "#fbbf24", "#d97706",
     ["aperçu graphique de la piscine (#4)", "planning et cadrage (#15)", "relectures exigeantes"]),
]


def cartes():
    for login, nom, role, c1, c2, contribs in EQUIPE:
        b64 = base64.b64encode((AVATARS / f"{login}.jpg").read_bytes()).decode()
        W, H, cx, cy = 380, 470, 190, 150
        o = [
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" '
            f'width="{W}" height="{H}" role="img" aria-label="{escape(nom)}, {escape(role)}">'
        ]
        o.append(f"""<defs>
  <clipPath id="rond"><circle cx="{cx}" cy="{cy}" r="74"/></clipPath>
  <linearGradient id="anneau" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}" stop-opacity=".1"/></linearGradient>
  <linearGradient id="bandeau" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{c2}" stop-opacity=".55"/><stop offset="1" stop-color="{c1}" stop-opacity=".05"/></linearGradient>
  <filter id="lueur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3"/></filter>
</defs>""")
        o.append(f'<rect width="{W}" height="{H}" rx="22" fill="{FOND}" stroke="#1e293b" stroke-width="2"/>')
        o.append(f'<path d="M0 22a22 22 0 0 1 22-22h{W - 44}a22 22 0 0 1 22 22v58H0z" fill="url(#bandeau)"/>')
        # Anneaux tournants et agents en orbite
        o.append(
            f'<circle cx="{cx}" cy="{cy}" r="90" fill="none" stroke="url(#anneau)" stroke-width="4" stroke-dasharray="70 16" stroke-linecap="round">'
            f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="14s" repeatCount="indefinite"/></circle>'
        )
        o.append(
            f'<circle cx="{cx}" cy="{cy}" r="100" fill="none" stroke="{c1}" stroke-opacity=".35" stroke-width="1.5" stroke-dasharray="2 9">'
            f'<animateTransform attributeName="transform" type="rotate" from="360 {cx} {cy}" to="0 {cx} {cy}" dur="22s" repeatCount="indefinite"/></circle>'
        )
        for i, (dur, r_orb, taille) in enumerate([(6, 100, 5), (9, 90, 4), (13, 110, 3.5)]):
            o.append(
                f'<g><circle cx="{cx + r_orb}" cy="{cy}" r="{taille}" fill="#f8fafc" filter="url(#lueur)"/>'
                f'<circle cx="{cx + r_orb}" cy="{cy}" r="{taille * 0.7}" fill="#ffffff"/>'
                f'<animateTransform attributeName="transform" type="rotate" from="{i * 120} {cx} {cy}" to="{i * 120 + 360} {cx} {cy}" dur="{dur}s" repeatCount="indefinite"/></g>'
            )
        o.append(f'<circle cx="{cx}" cy="{cy}" r="77" fill="{c2}" fill-opacity=".25"/>')
        o.append(
            f'<image x="{cx - 74}" y="{cy - 74}" width="148" height="148" clip-path="url(#rond)" preserveAspectRatio="xMidYMid slice" '
            f'href="data:image/jpeg;base64,{b64}" xlink:href="data:image/jpeg;base64,{b64}"/>'
        )
        o.append(f'<circle cx="{cx}" cy="{cy}" r="74" fill="none" stroke="{c1}" stroke-width="3"/>')
        o.append(
            f'<text x="{cx}" y="290" text-anchor="middle" font-family="{POLICE}" font-size="25" font-weight="800" fill="#f8fafc">{escape(nom)}</text>'
        )
        o.append(
            f'<text x="{cx}" y="316" text-anchor="middle" font-family="{MONO}" font-size="14" fill="{c1}">@{escape(login)}</text>'
        )
        o.append(
            f'<rect x="{cx - 128}" y="332" width="256" height="28" rx="14" fill="{c1}" fill-opacity=".12" stroke="{c1}" stroke-opacity=".5"/>'
            f'<text x="{cx}" y="351" text-anchor="middle" font-family="{POLICE}" font-size="13.5" font-weight="700" fill="{c1}">{escape(role)}</text>'
        )
        for k, txt in enumerate(contribs):
            y = 392 + k * 24
            o.append(f'<circle cx="52" cy="{y - 5}" r="3.5" fill="{c1}"/>')
            o.append(f'<text x="66" y="{y}" font-family="{POLICE}" font-size="14.5" fill="#cbd5e1">{escape(txt)}</text>')
        o.append("</svg>")
        (SORTIE / f"equipe-{login}.svg").write_text("\n".join(o), encoding="utf-8")


n = ascii_anim()
cartes()
print("images ASCII :", n, "| duree du cycle :", f"{n * PAS:.1f} s")
for p in sorted(SORTIE.glob("*.svg")):
    print(p.name, p.stat().st_size, "octets")
