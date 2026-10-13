# ViscoCrowd · profil de l'organisation

Ce dépôt contient la page d'accueil de l'organisation [ViscoCrowd](https://github.com/ViscoCrowd) : GitHub affiche
[`profile/README.md`](profile/README.md) en tête de la page de l'organisation.

## Contenu

| Chemin | Rôle |
|---|---|
| `profile/README.md` | la page d'accueil |
| `profile/assets/*.svg` | animations SVG (bannière, ASCII, diagramme fondamental, terminal, feuille de route, cartes d'équipe) |
| `profile/assets/logo-viscocrowd.svg` | logo animé de l'organisation, généré |
| `profile/assets/avatars/` | photos de profil GitHub, embarquées dans les cartes d'équipe |
| `scripts/` | générateurs des animations et du logo, script de vérification |
| `.github/workflows/profil.yml` | CI : régénère les animations et vérifie le profil à chaque PR |

## Régénérer les animations

Les générateurs n'utilisent que la bibliothèque standard de Python 3.12 :

```bash
python scripts/gen_assets.py profile/assets
python scripts/gen_extra.py profile/assets profile/assets/avatars
python scripts/gen_logo.py profile/assets
python scripts/verifier.py
```

Tout est calculé, rien n'est dessiné à la main : trajectoires des agents (graine fixe), courbe de Weidmann
(constantes du dépôt de simulation), sortie réelle de `viscocrowd valider-moteur`.

## Pourquoi tout est embarqué

GitHub bloque toute ressource externe dans un SVG affiché comme image : polices, images, scripts. Les animations
utilisent donc des polices système et SMIL, et les photos de profil sont embarquées en base64.
`scripts/verifier.py` refuse tout SVG qui appellerait une ressource externe.

Si une photo de profil change, remplacer le fichier dans `profile/assets/avatars/` puis relancer `gen_extra.py`.
