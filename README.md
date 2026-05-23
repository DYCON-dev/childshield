<div align="center">

<img src="assets/logo.svg" width="120" alt="ChildShield logo">

# ChildShield

**Privacy-first face blurring to protect children's faces before you share a photo online.**
**100 % local. No cloud. No tracking.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platforms](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-blue)](#download)
[![Made with PyQt6](https://img.shields.io/badge/built%20with-PyQt6-41cd52)](https://riverbankcomputing.com/software/pyqt/)

[Download](#download) · [How it works](#how-it-works) · [Limitations](#limitations-honest-disclosure) · [Contribute](#contributing) · [🇫🇷 Français](#-français)

</div>

---

## 🇬🇧 English

ChildShield helps parents, journalists, teachers, and NGOs blur faces in photos **before** publishing them on social media or sharing publicly. Everything runs locally on your machine — no upload, no API call, no telemetry.

### Why?

Children appear in photos every day on Instagram, WhatsApp groups, school newsletters, news articles. Once a face is online, you cannot take it back. Manual blurring (Photoshop, paint apps) is slow and error-prone — ChildShield does it in one drag-and-drop.

### What's in this repository

| App | Status | Platform |
|-----|--------|----------|
| [Desktop app](apps/desktop) | 🟢 **v0.1.0** released | macOS, Windows, Linux |
| [Browser extension](apps/extension) | 🔴 Planned (next milestone) | Chrome, Firefox, Safari |
| [Safari wrapper](apps/safari) | 🔴 Planned | macOS Safari |

The desktop app and the browser extension share the same models — two ONNX files run identically in Python (`onnxruntime`) and in the browser (`onnxruntime-web` / WASM).

### How it works

1. Drag a photo into the window (or click "Open image")
2. **InsightFace SCRFD-10G** detects every face (~16 MB ONNX, bundled)
3. **ViT-FairFace** age classifier predicts an age bucket per face (~85 MB ONNX, bundled)
4. Faces whose bucket may include a minor (0-2, 3-9, 10-19) are pre-flagged for blur
5. **Click any face** — or its row in the side panel — to flip its blur state
6. **Save blurred copy** writes `blurred_<filename>` next to the original

The blur is an elliptical region with a smoothstep alpha falloff, so the dissolve into the surrounding photo is soft and round rather than a hard rectangle.

### Privacy guarantees

- ✅ Runs entirely on your device — no internet connection required
- ✅ Models are bundled inside the app (no download at runtime)
- ✅ No analytics, no crash reporting, no telemetry
- ✅ No file is ever sent to a server
- ✅ Source code and model weights are open and auditable

### Limitations (honest disclosure)

- The face detector misses tilted, profile, or partially occluded faces.
- The age model groups faces into nine coarse buckets (`0-2`, `3-9`, `10-19`, `20-29` …). It is more reliable than a continuous age regressor for our "minor vs. adult" decision but still wrong sometimes — that is exactly why **every face can be toggled manually**.
- Age estimation models in general have measurable demographic biases. We chose **ViT-FairFace** specifically because [FairFace](https://github.com/joojs/fairface) was assembled to be demographically balanced, but biases are not gone, only reduced.
- **This is a tool, not a guarantee — always review the output before sharing.**

### Download

Pre-built binaries for macOS, Windows, and Linux are produced from the
[release workflow](.github/workflows/release.yml) and attached to each
GitHub Release: **<https://github.com/DYCON-dev/childshield/releases>**.

The binaries are **unsigned** in v0.1.0. On macOS you may need to
right-click → *Open* → *Open* the first time, or allow it in
*System Settings → Privacy & Security*. Same idea on Windows
(SmartScreen).

#### Run from source

```bash
git clone https://github.com/DYCON-dev/childshield.git
cd childshield/apps/desktop
python -m venv .venv && source .venv/bin/activate
pip install -e .
childshield
```

Requires Python 3.9+.

### Roadmap

- ✅ **v0.1.0** — Desktop app with SCRFD detection, ViT-FairFace age classification, clickable per-face override, soft elliptical blur
- 🔜 **v0.2** — Browser extension (Chrome, Firefox, Safari) sharing the same ONNX models via `onnxruntime-web`
- 🔜 **v0.3** — Video support, batch mode, CLI

### Contributing

Issues and pull requests welcome. This is an OSS project — no contributor agreement, no maintainers council, just normal GitHub workflow.

If you want to swap a model (the project is intentionally model-agnostic via ONNX), the place to start is [`apps/desktop/childshield/analysis.py`](apps/desktop/childshield/analysis.py) and [`apps/desktop/tools/convert_age_model.py`](apps/desktop/tools/convert_age_model.py).

### License

[MIT](LICENSE) — use freely, commercial or not.

### Acknowledgements

- [InsightFace](https://github.com/deepinsight/insightface) — SCRFD face detector (MIT)
- [`nateraw/vit-age-classifier`](https://huggingface.co/nateraw/vit-age-classifier) — Vision Transformer fine-tuned on the FairFace dataset (MIT)
- [FairFace](https://github.com/joojs/fairface) — demographically balanced face attribute dataset by Karkkainen & Joo (2021)
- [OpenCV](https://opencv.org), [PyQt6](https://riverbankcomputing.com/software/pyqt/), [ONNX Runtime](https://onnxruntime.ai/), [PyInstaller](https://pyinstaller.org/)

---

## 🇫🇷 Français

ChildShield aide les parents, journalistes, enseignants et ONG à flouter les visages dans les photos **avant** de les publier sur les réseaux sociaux ou de les partager publiquement. Tout se passe localement sur votre machine — aucun envoi, aucune API, aucun pistage.

### Pourquoi ?

Des enfants apparaissent quotidiennement dans des photos publiées sur Instagram, dans des groupes WhatsApp, dans les newsletters d'école, dans la presse. Une fois en ligne, un visage ne peut plus être retiré. Flouter manuellement (Photoshop, apps de retouche) est lent et imprécis — ChildShield le fait en un glisser-déposer.

### Contenu du dépôt

| Application | Statut | Plateforme |
|-------------|--------|------------|
| [Application bureau](apps/desktop) | 🟢 **v0.1.0** disponible | macOS, Windows, Linux |
| [Extension navigateur](apps/extension) | 🔴 Prévu (jalon suivant) | Chrome, Firefox, Safari |
| [Wrapper Safari](apps/safari) | 🔴 Prévu | macOS Safari |

### Comment ça marche

1. Glissez une photo dans la fenêtre (ou cliquez sur « Open image »)
2. **InsightFace SCRFD-10G** détecte chaque visage (~16 Mo d'ONNX embarqués)
3. **ViT-FairFace** classifie l'âge par tranches (~85 Mo d'ONNX embarqués)
4. Les visages dont la tranche d'âge pourrait inclure un mineur (0-2, 3-9, 10-19) sont pré-sélectionnés pour flou
5. **Cliquez sur un visage** ou sur sa ligne dans le panneau de droite pour basculer son état
6. **Save blurred copy** enregistre `blurred_<nom>` à côté de l'original

### Garanties de confidentialité

- ✅ Tout s'exécute sur votre appareil — aucune connexion requise
- ✅ Les modèles sont embarqués (pas de téléchargement à l'exécution)
- ✅ Aucune analytique, aucun rapport de crash, aucun pistage
- ✅ Aucun fichier n'est envoyé à un serveur
- ✅ Code source et poids des modèles ouverts et auditables

### Limitations (transparence)

- Le détecteur rate les visages très inclinés, de profil, ou partiellement cachés.
- Le modèle d'âge classe en 9 tranches (`0-2`, `3-9`, `10-19`, `20-29` …). C'est plus fiable qu'une estimation continue pour la décision « mineur vs adulte » mais ce n'est pas infaillible — c'est précisément pour ça que **chaque visage peut être basculé manuellement**.
- Tout modèle d'estimation d'âge a des biais démographiques mesurables. Nous avons choisi **ViT-FairFace** parce que [FairFace](https://github.com/joojs/fairface) a été construit pour être démographiquement équilibré, mais les biais ne disparaissent pas, ils diminuent.
- **C'est un outil, pas une garantie — vérifiez toujours le résultat avant de partager.**

### Téléchargement

Les binaires précompilés (macOS / Windows / Linux) sont attachés à chaque
release GitHub : **<https://github.com/DYCON-dev/childshield/releases>**.

Ils sont **non signés** en v0.1.0. Sur macOS, premier lancement : clic-droit → *Ouvrir* → *Ouvrir*, ou autorisez dans *Réglages Système → Confidentialité et sécurité*. Idem côté Windows (SmartScreen).

### Feuille de route

- ✅ **v0.1.0** — App bureau avec détection SCRFD, classification d'âge ViT-FairFace, clic par visage, flou elliptique doux
- 🔜 **v0.2** — Extension navigateur (Chrome, Firefox, Safari) partageant les mêmes modèles ONNX via `onnxruntime-web`
- 🔜 **v0.3** — Vidéo, mode lot, ligne de commande

### Licence

[MIT](LICENSE) — usage libre, commercial ou non.
