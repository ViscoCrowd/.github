"""Verifie le profil de l'organisation avant qu'il ne parte sur la page GitHub.

Trois pieges, chacun invisible tant qu'on ne regarde pas la page en ligne :

  1. un SVG mal forme s'affiche comme une image cassee ;
  2. un SVG qui appelle une ressource externe (police, image, script) est bloque
     par GitHub : tout ce qu'il affiche doit etre embarque (URI data:) ;
  3. une image citee par le README mais absente du depot laisse un trou.

Usage : python scripts/verifier.py   (depuis la racine du depot)
"""

from __future__ import annotations

import re
import sys
import xml.dom.minidom
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
PROFIL = RACINE / "profile"
POIDS_MAX = 1_000_000  # octets : au-dela, la page du profil devient lente a charger
ANIMES = {"animate", "animateMotion", "animateTransform", "set"}

erreurs: list[str] = []

svgs = sorted((PROFIL / "assets").glob("*.svg"))
if not svgs:
    erreurs.append("aucun SVG dans profile/assets")

for svg in svgs:
    nom = svg.relative_to(RACINE)
    taille = svg.stat().st_size
    if taille > POIDS_MAX:
        erreurs.append(f"{nom} : {taille} octets, au-dela de {POIDS_MAX}")
    try:
        doc = xml.dom.minidom.parse(str(svg))
    except Exception as exc:  # noqa: BLE001 - on veut le message, quel qu'il soit
        erreurs.append(f"{nom} : XML invalide ({exc})")
        continue
    texte = svg.read_text(encoding="utf-8")
    externes = re.findall(r'(?:href|src)="(https?:[^"]+)"', texte) + re.findall(r"url\((https?:[^)]+)\)", texte)
    if externes:
        erreurs.append(f"{nom} : ressource externe bloquee par GitHub : {externes[0]}")
    animations = sum(len(doc.getElementsByTagName(t)) for t in ANIMES)
    print(f"ok  {nom}  {taille:>7} octets  {animations:>4} animations")

readme = PROFIL / "README.md"
if not readme.exists():
    erreurs.append("profile/README.md manquant")
else:
    contenu = readme.read_text(encoding="utf-8")
    locaux = re.findall(r'(?:src|href)="((?!https?:|#|mailto:)[^"]+)"', contenu)
    locaux += re.findall(r"\]\(((?!https?:|#|mailto:)[^)\s]+)\)", contenu)
    for lien in locaux:
        if not (PROFIL / lien).exists():
            erreurs.append(f"profile/README.md cite {lien}, absent du depot")
    print(f"ok  profile/README.md  {len(locaux)} liens locaux verifies")

if erreurs:
    print("\nECHEC :", *erreurs, sep="\n  - ")
    sys.exit(1)
print("\nProfil pret a publier.")
