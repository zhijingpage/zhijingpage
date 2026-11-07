# Zhi Jing — Academic Website

An English academic homepage for **Zhi Jing (井智), Fudan University**. The page opens with a personal introduction, followed by News, Publications, Education, and Honors & Awards. The Hand animation link in the introduction opens the original Blender film in a player.

## Preview

Open `index.html` directly, or run:

```sh
python3 -m http.server 8765
```

Then visit `http://localhost:8765`. A local server enables clipboard features consistently. There is no dependency installation or build step.

## Publish on GitHub Pages

1. Commit these files to the `main` branch of `zhijingpage/zhijingpage`. Keep `index.html`, `styles.css`, `app.js`, `.nojekyll`, and the `assets` directory at the repository root.
2. In the repository, open **Settings → Pages**.
3. Choose **Deploy from a branch**, then **main** and **/(root)**. Save.
4. After GitHub finishes deployment, the expected address is `https://zhijingpage.github.io/zhijingpage/`.

This project works under a repository subpath and at a root domain. The expected URL above is not a claim that the site has already been deployed.

## Editing

- `index.html`: biography, project descriptions, author lists, links, and accessible markup.
- `styles.css`: typography, colors, responsive layouts, and image framing.
- `app.js`: publication filtering and search, the citation dialog, BibTeX, and playback controls for *In-hand rotation.*
- `assets/in-hand-rotation.mp4` contains the film, and `assets/in-hand-poster.webp` supplies its still preview.
- The offline source package includes the Blender scripts `animation-source/hand.py` and `animation-source/studio.py` for editing the hand and its scene.
- `assets/zhi-jing.jpg`: the portrait supplied by Zhi Jing, retained unchanged. Cropping is performed with CSS.
- `assets/favicon.svg`: original 井-based identity mark.

When adding a publication, update the HTML entry, the relevant filter if needed, and its BibTeX in `app.js`.

## Content notes

The three papers were confirmed against the user's supplied Google Scholar list and primary sources on 6 November 2026. Conference year and Scholar indexing year may differ: **HumanoidGen is presented as NeurIPS 2025**, matching the official proceedings. **AssemLM is marked CoRL 2026** according to its authors' official acceptance announcement. Its citation points to the available arXiv version. VQ-Memory is marked as a preprint.

No academic degree, advisor relationship, personal email, awards, or citation metrics have been inferred. No analytics, cookies, third-party fonts, or external JavaScript are used.

See `SOURCES.md` for publication, image, and animation credits.
