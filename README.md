# ChildShield

> Privacy-first face blurring to protect children's faces before you share a photo online.
> 100% local. No cloud. No tracking.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🇬🇧 English

ChildShield helps parents, journalists, teachers, and NGOs blur faces in photos **before** publishing them on social media or sharing publicly. Everything runs locally on your machine — no upload, no API call, no telemetry.

### Why?

Children appear in photos every day on Instagram, WhatsApp groups, school newsletters, news articles. Once a face is online, you cannot take it back. Manual blurring (Photoshop, paint apps) is slow and error-prone — ChildShield does it in one drag-and-drop.

### What's in this repository

| App | Status | Platform |
|-----|--------|----------|
| [Desktop app](apps/desktop) | 🟢 V1.5 — face detection + age estimation | macOS, Linux, Windows |
| [Browser extension](apps/extension) | 🔴 Planned | Chrome, Firefox, Safari |
| [Safari wrapper](apps/safari) | 🔴 Planned | macOS Safari |

The desktop app and the browser extension share the same brand and goal but are intentionally separate implementations (Python + OpenCV for desktop, JavaScript + face-api.js for browser).

### Privacy guarantees

- ✅ Runs entirely on your device
- ✅ Models bundled inside the app (no download at runtime)
- ✅ No analytics, no crash reporting, no telemetry
- ✅ No file is ever sent to a server
- ✅ Source code is open and auditable

### Limitations (honest disclosure)

- Face detection models miss tilted, profile, or partially occluded faces
- Age estimation models (planned for V1.5) are known to be **biased**: less accurate on darker skin tones and on Asian features. We default to a **conservative mode** (blur all detected faces; user manually unblurs the ones they want to keep visible) for this reason.
- This is a tool, not a guarantee — always review the output before sharing.

### Roadmap

- ✅ **V1**: Desktop app — drag a photo, conservative "blur all" mode
- ✅ **V1.5** (current): Age estimation — blurs only faces estimated below a configurable age (default ≤ 12). Toggle "blur all" still available as override.
- **V1.6**: Click any face to manually toggle blur on/off (per-face override)
- **V1.7**: Switch age model from Caffe (2015) to MiVOLO (2024) for better accuracy and reduced bias
- **V2**: Browser extension (Chrome, Firefox, Safari)
- **V3**: Video support, batch mode, CLI

### License

[MIT](LICENSE) — use freely, commercial or not.

### Acknowledgements

- [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet) face detector (OpenCV Zoo, MIT)
- Age estimation model by Gil Levi & Tal Hassner — *Age and Gender Classification using Convolutional Neural Networks*, CVPR 2015 — [project page](https://talhassner.github.io/home/publication/2015_CVPR)
- [face-api.js](https://github.com/justadudewhohacks/face-api.js) (planned V2 extension, MIT)
- [OpenCV](https://opencv.org), [PyQt6](https://pypi.org/project/PyQt6/)

---

## 🇫🇷 Français

ChildShield aide les parents, journalistes, enseignants et ONG à flouter les visages dans les photos **avant** de les publier sur les réseaux sociaux ou de les partager publiquement. Tout se passe localement sur votre machine — aucun envoi, aucune API, aucun pistage.

### Pourquoi ?

Des enfants apparaissent quotidiennement dans des photos publiées sur Instagram, dans des groupes WhatsApp, dans les newsletters d'école, dans la presse. Une fois en ligne, un visage ne peut plus être retiré. Flouter manuellement (Photoshop, apps de retouche) est lent et imprécis — ChildShield le fait en un glisser-déposer.

### Contenu du dépôt

| Application | Statut | Plateforme |
|-------------|--------|------------|
| [Application bureau](apps/desktop) | 🟡 V1 en cours | macOS, Linux, Windows |
| [Extension navigateur](apps/extension) | 🔴 Prévu | Chrome, Firefox, Safari |
| [Wrapper Safari](apps/safari) | 🔴 Prévu | macOS Safari |

### Garanties de confidentialité

- ✅ Tout s'exécute sur votre appareil
- ✅ Les modèles sont embarqués (pas de téléchargement à l'exécution)
- ✅ Aucune analytique, aucun rapport de crash, aucun pistage
- ✅ Aucun fichier n'est envoyé à un serveur
- ✅ Code source ouvert et auditable

### Limitations (transparence)

- Les modèles de détection ratent les visages très inclinés, de profil, ou partiellement cachés
- Les modèles d'estimation d'âge (prévus en V1.5) ont des **biais documentés** : moins précis sur les peaux foncées et les traits asiatiques. Par défaut, ChildShield est en **mode conservateur** (floute tous les visages détectés ; l'utilisateur dé-floute manuellement ceux qu'il veut laisser visibles).
- C'est un outil, pas une garantie — vérifiez toujours le résultat avant de partager.

### Feuille de route

- **V1** (en cours) : application bureau — glisser une photo, tous les visages détectés sont floutés, copie sauvegardée
- **V1.5** : assistance par estimation d'âge (« ChildShield pense que ces 2 visages sont jeunes ») + clic pour basculer le flou par visage
- **V2** : extension navigateur (Chrome, Firefox, Safari)
- **V3** : vidéo, mode lot, ligne de commande

### Licence

[MIT](LICENSE) — usage libre, commercial ou non.
