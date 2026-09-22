# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Personal academic website of Siddhant Midha (siddhantmidha.com), built on the
[al-folio](https://github.com/alshedivat/al-folio) Jekyll theme. The theme's own
docs live in `CONTRIBUTING.md`; `README.md` is a stub. Most work here is content
authoring (posts, notes, teaching pages, publications), not theme development.

## Local development

The system Ruby on this machine is 2.6; CI builds with Ruby 3.2.2 and there is no
checked-in `Gemfile.lock`. Docker is the reliable local path:

```bash
docker compose pull && docker compose up   # serves at http://localhost:8080 with livereload
```

Native, if a modern Ruby is available:

```bash
bundle install
bundle exec jekyll serve --lsi   # --lsi powers related-post matching
bundle exec jekyll build --lsi   # same as bin/cibuild
```

`bin/entry_point.sh` (used inside the container) restarts Jekyll on `_config.yml`
changes; every other file is picked up by `--watch`.

Pre-commit hooks (whitespace, EOF, YAML, large files) are configured in
`.pre-commit-config.yaml`; install with `pre-commit install`.

## Deploy

`.github/workflows/deploy.yml` runs on every push/PR to `master`. It builds with
`JEKYLL_ENV=production`, runs `purgecss -c purgecss.config.js` over `_site`, and
pushes `_site` to the `gh-pages` branch. So: **commit sources to `master` only;
never hand-edit `gh-pages`.** `bin/deploy` does the same thing locally and is
normally unnecessary. Note the workflow overwrites `giscus.repo` in `_config.yml`
at build time.

## Content model

Everything is driven by front matter; adding a file to the right directory is
usually the whole change.

- `_posts/YYYY-MM-DD-slug.md` — blog. All current posts use `layout: distill`
  (two-column academic layout with sidebar TOC, footnotes, citations). Permalinks
  are `/blog/:year/:title/`. Tags/categories listed in `display_tags` /
  `display_categories` in `_config.yml` surface on the blog index; anything else
  is still archived under `/blog/tag/:name/`.
- `_news/announcement_N.md` — short dated items on the about page. `inline: true`
  renders the body directly in the list. `_config.yml: announcements.limit` caps
  how many show.
- `_teaching/*.md` and `_projects/*.md` — card collections rendered by
  `_pages/teaching.md` / the projects includes. `category` groups the cards
  (`iitb`, `undergrad projects`, `undergrad research`) and `importance` orders
  within a group. Note `_pages/teaching.md` currently hand-writes its course list
  with absolute links rather than using the collection's card rendering.
- `_pages/*.md` — top-level pages. `nav: true` plus `nav_order` controls the
  navbar; `_pages/dropdown.md` defines a submenu via its `children` list.
- `_bibliography/papers.bib` — publications, rendered by jekyll-scholar on
  `/publications/`. Custom bib fields (`abbr`, `arxiv`, `html`, `pdf`, `selected`,
  `preview`, `bibtex_show`, …) are consumed by `_layouts/bib.html` and stripped
  from displayed BibTeX by `_plugins/hideCustomBibtex.rb`. `selected={true}`
  promotes a paper to the about page (currently disabled there). **Do not
  regenerate this file** — see below.
- `_data/` — `cv.yml` (feeds `/cv/`, alongside `assets/json/resume.json` pulled in
  by jekyll-get-json), `repositories.yml`, `coauthors.yml`, `venues.yml`.

## Publication sync

`bin/sync-publications.py` keeps `papers.bib` current. Google Scholar has no API
and blocks automated access, so the script approximates it: **ORCID + Semantic
Scholar** for discovery (what papers exist), **`arxiv.org/bibtex/<id>` + Crossref
content negotiation** for the actual BibTeX. Upstream BibTeX is taken verbatim
rather than rebuilt from the discovery JSON, because Semantic Scholar mangles
titles and initializes author names.

It **merges, never regenerates.** Citation keys and every curated field survive;
a preprint that has since been published is upgraded in place (type `@misc` →
`@article`, journal/volume/DOI filled in, `eprint`/`archivePrefix` dropped) while
keeping its `preview` image. The script is stdlib-only, idempotent (a no-op second
run is byte-identical), and rate-limits per host — arXiv answers bursts with a 406.

```bash
python3 bin/sync-publications.py --dry-run --verbose   # report only
python3 bin/sync-publications.py                       # write papers.bib
```

`.github/workflows/sync-publications.yml` runs it weekly and opens a PR when
something changed; `deploy.yml` builds that PR, so a green check means the
bibliography still parses. New entries need a `preview={...}` image added by hand
in `assets/img/publication_preview/` — the script's report lists which.

Records on the upstream profiles with neither an arXiv ID nor a DOI cannot be
resolved and are reported as `SKIP` on stderr. Mis-attributed papers go in the
script's `IGNORE` set.

## Assets and PDFs

Written notes/talks live as compiled PDFs under `assets/pdf/`, `assets/notes/`,
and LaTeX sources under `assets/TeX/`. `_pages/notes.md` links to them by absolute
URL. Keep source and built PDF together, and check the link actually resolves —
the page mixes `siddhantmidha.com`, `siddhant-midha.github.io`, and at least one
malformed `assets/assets/...` path.

Images in `assets/img/` are processed by jekyll-imagemagick into 480/800/1400px
WebP variants at build time (ImageMagick must be installed for a native build).
Use `{% include figure.html %}` rather than raw `<img>` so responsive sources and
medium-zoom work.

## Custom Liquid extensions (`_plugins/`)

- `{% details Caption %}…{% enddetails %}` — collapsible block.
- `{% file_exists path %}` — returns `"true"`/`"false"`, used to guard optional assets.
- `cache-bust.rb` — appends MD5 query strings to asset URLs.
- `external-posts.rb` — pulls RSS entries listed under `external_sources` into
  `_posts` at build time (currently unconfigured).

## Conventions

- Site-wide toggles (dark mode, math/MathJax, masonry, medium-zoom, progress bar,
  publication badges) are the `enable_*` flags at the bottom of `_config.yml`;
  prefer flipping those over editing includes.
- Styling belongs in `_sass/` (`_themes.scss` holds the light/dark variables);
  `assets/css/main.scss` is the entry point. Because purgecss runs in production,
  class names constructed dynamically in JS can get stripped — add them to
  `purgecss.config.js` safelist if so.
- Page titles and nav labels on this site are lowercase.
