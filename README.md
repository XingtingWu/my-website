# Xingting Wu — academic website

A static academic website centred on participatory design, outdoor engagement,
and research with older adults. All pages work without a build server or framework.

## Preview

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Open http://127.0.0.1:8765. Serve this repository only, not its parent planning folder.

## Update the site

- Edit shared layouts and page copy in `scripts/build.py`.
- Edit the Scholar-based bibliography in `data/publications.json`.
- Web-ready images live in `assets/images/`; dimensions are in `data/images.json`.
- Styles and progressive enhancements live in `assets/site.css` and `assets/site.js`.

```sh
python3 scripts/build.py
python3 scripts/check.py
```

The build generates complete HTML pages, a sitemap, and robots.txt. Commit the
generated pages along with their source. Existing static hosting can serve the
repository root directly, without a build command. Relative links also support
a GitHub Pages project path. Canonical URLs use https://www.xingtingwu.com/.

## Content and image privacy

The bibliography reflects 18 records on the supplied Google Scholar profile as
of 20 September 2026. Publication types and preprint links are labelled. The
ongoing 2026 project is separate from the three empirical studies in the MCR.

Only metadata-free image derivatives belong in the website. At the site owner’s
request on 20 September 2026, research photographs are shown without the previously
added masks. The assembly photo is re-exported from its original, replacing the
already blurred thesis montage. Raw full-resolution files, transcripts, participant
records, the thesis, and the private asset-source manifest stay outside this repository.
Enlarged images use the same web derivatives.

The homepage introduces Xingting first, followed by three selected projects:
Nativity crafting, shared gardening, and the ongoing 2026 Our Outdoor Stories work.
The 2025 Outdoor Discovery study remains in the complete Research journey.

The UI is responsive, includes keyboard focus states and reduced-motion support,
and provides search, publication filters, and a keyboard-accessible image dialog.
No analytics or external JavaScript is loaded.

## Making-process photographs

The homepage Design Practice feature shows the Nativity garden-bed concept.
Practice opens with researcher photographs from ProtoLAB and Cricut preparation,
followed by cutting layouts, laser fabrication, early assembly parts, and design
iteration. The Nativity case links preparation to the later workshop changes.
Three images are labelled stills extracted from original 2024 preparation videos.
Source videos and private extraction records remain outside the website.
