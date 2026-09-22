#!/usr/bin/env python3
"""Sync _bibliography/papers.bib against ORCID + Semantic Scholar.

Google Scholar has no API and blocks automated access, so we approximate it:

  discovery  ORCID works + Semantic Scholar author papers -> what exists
  metadata   arxiv.org/bibtex + Crossref content negotiation -> the actual BibTeX

Upstream BibTeX is used verbatim rather than rebuilt from the discovery JSON,
because Semantic Scholar mangles titles ("Beyond belief Propagation: ...") and
initializes author names ("D. Abanin").

The file is MERGED, never regenerated. Entries keep their citation keys and every
hand-curated field (preview, abbr, selected, blog, code, ...) that _layouts/bib.html
renders and no API can supply. A preprint that has since been published is upgraded
in place: bibliographic fields are refreshed, curation is untouched.

Usage:
    python3 bin/sync-publications.py [--dry-run] [--verbose]

Exit status is 0 whether or not anything changed; the workflow diffs the file.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ORCID_ID = "0009-0001-7164-4933"
SEMANTIC_SCHOLAR_ID = "2217725587"
AUTHOR_SURNAME = "midha"

BIB_PATH = Path(__file__).resolve().parent.parent / "_bibliography" / "papers.bib"

# Records to keep off the publications page: mis-attributions on the upstream
# profiles, or writing that belongs elsewhere on the site.
IGNORE_IDS = {              # arXiv IDs / DOIs, lowercase, matched exactly
    "2309.15162",           # Integer Factorization through Func-QAOA
}
IGNORE_TITLES = {           # matched ignoring case and punctuation
    # Expository review; carries no arXiv ID or DOI upstream, and is already
    # linked from /notes/ as expository writing.
    "High Fidelity Rydberg Gates: A Review of Recent Techniques",
}

# Fields owned by the upstream record. Everything else on an existing entry is
# curation and survives an upgrade untouched.
BIBLIOGRAPHIC = {
    "title", "author", "journal", "booktitle", "volume", "number", "pages",
    "year", "month", "doi", "url", "publisher", "issn", "isbn", "eprint",
    "archiveprefix", "primaryclass", "note", "urldate", "language", "copyright",
    "shorttitle", "keywords",
}

USER_AGENT = "al-folio-publication-sync (+https://siddhantmidha.com)"


# --------------------------------------------------------------------------
# BibTeX parsing
#
# A real parser rather than regex-per-field, because abstracts contain braces
# and the file mixes Zotero exports with hand-written arXiv entries.
# --------------------------------------------------------------------------

class Entry:
    def __init__(self, etype, key, fields, raw):
        self.etype = etype          # "article", "misc", ...
        self.key = key              # citation key
        self.fields = fields        # lowercased name -> (value, delimiter)
        self.raw = raw              # original text, emitted as-is if untouched
        self.dirty = False

    def get(self, name):
        pair = self.fields.get(name.lower())
        return pair[0] if pair else None

    def set(self, name, value, delim="{"):
        self.fields[name.lower()] = (value, delim)
        self.dirty = True

    def drop(self, name):
        if self.fields.pop(name.lower(), None) is not None:
            self.dirty = True

    def render(self):
        if not self.dirty:
            return self.raw
        width = max((len(n) for n in self.fields), default=0)
        lines = [f"@{self.etype}{{{self.key},"]
        for name, (value, delim) in self.fields.items():
            close = {"{": "}", '"': '"', "": ""}[delim]
            lines.append(f"  {name.ljust(width)} = {delim}{value}{close},")
        lines.append("}")
        return "\n".join(lines)


_ENTRY_START = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)
_FIELD_START = re.compile(r"\s*([A-Za-z_][\w-]*)\s*=\s*")


def _match_brace(text, open_index):
    """Index of the brace closing the one at open_index."""
    depth = 0
    for i in range(open_index, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError(f"unbalanced braces from offset {open_index}")


def _parse_fields(body):
    fields, pos = {}, 0
    while pos < len(body):
        m = _FIELD_START.match(body, pos)
        if not m:
            break
        name, pos = m.group(1).lower(), m.end()
        if pos >= len(body):
            break
        if body[pos] == "{":
            end = _match_brace(body, pos)
            value, delim, pos = body[pos + 1:end], "{", end + 1
        elif body[pos] == '"':
            end = pos + 1
            while end < len(body) and not (body[end] == '"' and body[end - 1] != "\\"):
                end += 1
            value, delim, pos = body[pos + 1:end], '"', end + 1
        else:                                    # bare token, e.g. month = mar
            end = pos
            while end < len(body) and body[end] not in ",\n":
                end += 1
            value, delim, pos = body[pos:end].strip(), "", end
        fields[name] = (value, delim)
        while pos < len(body) and body[pos] in ", \t\r\n":
            pos += 1
    return fields


def parse_bib(text):
    entries, pos = [], 0
    while True:
        m = _ENTRY_START.search(text, pos)
        if not m:
            return entries
        open_index = text.index("{", m.start())
        end = _match_brace(text, open_index)
        entries.append(Entry(
            m.group(1).lower(), m.group(2),
            _parse_fields(text[m.end():end]),
            text[m.start():end + 1],
        ))
        pos = end + 1


# --------------------------------------------------------------------------
# Identity
# --------------------------------------------------------------------------

ARXIV_DOI = re.compile(r"10\.48550/arxiv\.(\S+)", re.I)
ARXIV_ANY = re.compile(r"(?:arxiv[.:/]|abs/)\s*(\d{4}\.\d{4,5})", re.I)


def norm_arxiv(value):
    return re.sub(r"v\d+$", "", value.strip()) if value else None


def norm_doi(value):
    if not value:
        return None
    value = value.strip().lower().replace("https://doi.org/", "")
    return None if ARXIV_DOI.match(value) else value or None


def norm_title(value):
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def entry_arxiv(entry):
    """arXiv ID of an entry, however the entry happens to record it."""
    if entry.get("eprint"):
        return norm_arxiv(entry.get("eprint"))
    haystack = " ".join(filter(None, (
        entry.get("url"), entry.get("note"), entry.get("doi"), entry.get("journal"),
    )))
    m = ARXIV_DOI.search(haystack) or ARXIV_ANY.search(haystack)
    return norm_arxiv(m.group(1)) if m else None


def is_preprint(entry):
    """True if the entry presents as an unpublished preprint."""
    if norm_doi(entry.get("doi")):
        return False
    journal = (entry.get("journal") or "").lower()
    return entry.etype == "misc" or "arxiv" in journal or not journal


# --------------------------------------------------------------------------
# Network
# --------------------------------------------------------------------------

# arXiv throttles bursts with a 406, so space requests out per host.
MIN_INTERVAL = 3.0
_last_request = {}


def _throttle(url):
    host = urllib.parse.urlparse(url).netloc
    wait = MIN_INTERVAL - (time.monotonic() - _last_request.get(host, 0.0))
    if wait > 0:
        time.sleep(wait)
    _last_request[host] = time.monotonic()


def fetch(url, accept=None, retries=4):
    request = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT, "Accept": accept or "*/*",
    })
    for attempt in range(retries):
        _throttle(url)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            # 406 is arXiv's throttle response; 429/503 are the usual ones.
            if exc.code in (406, 429, 503) and attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError:
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
                continue
            raise
    raise RuntimeError(f"giving up on {url}")


def discover():
    """Union of ORCID and Semantic Scholar, keyed by arXiv ID / DOI / title."""
    found = {}

    def record(arxiv, doi, title, year, abstract=None):
        title = (title or "").strip()
        if not title:
            return
        ident = norm_arxiv(arxiv), norm_doi(doi)
        # "\0" so a record with no identifier is not matched by an empty string.
        if (ident[0] or "\0") in IGNORE_IDS or (ident[1] or "\0") in IGNORE_IDS:
            return
        if norm_title(title) in {norm_title(t) for t in IGNORE_TITLES}:
            return
        key = ident[0] or ident[1] or norm_title(title)
        existing = found.get(key, {})
        found[key] = {
            "arxiv": ident[0] or existing.get("arxiv"),
            "doi": ident[1] or existing.get("doi"),
            "title": existing.get("title") or title,
            "year": year or existing.get("year"),
            "abstract": abstract or existing.get("abstract"),
        }

    fields = "title,year,externalIds,abstract"
    payload = json.loads(fetch(
        f"https://api.semanticscholar.org/graph/v1/author/{SEMANTIC_SCHOLAR_ID}"
        f"/papers?fields={fields},authors&limit=200"
    ))
    for paper in payload.get("data", []):
        names = " ".join(a.get("name", "") for a in paper.get("authors") or [])
        if AUTHOR_SURNAME not in names.lower():
            continue                              # guard against mis-attribution
        ids = paper.get("externalIds") or {}
        record(ids.get("ArXiv"), ids.get("DOI"), paper.get("title"),
               paper.get("year"), paper.get("abstract"))

    works = json.loads(fetch(f"https://pub.orcid.org/v3.0/{ORCID_ID}/works",
                             accept="application/json"))
    for group in works.get("group", []):
        for summary in group.get("work-summary", []):
            ids = {
                i.get("external-id-type"): i.get("external-id-value")
                for i in (summary.get("external-ids") or {}).get("external-id", [])
            }
            date = summary.get("publication-date") or {}
            record(ids.get("arxiv"), ids.get("doi"),
                   ((summary.get("title") or {}).get("title") or {}).get("value"),
                   (date.get("year") or {}).get("value"))

    # Merge records that arrived from the two sources under different keys.
    merged = {}
    for item in found.values():
        key = norm_title(item["title"])
        if key in merged:
            for field in ("arxiv", "doi", "year", "abstract"):
                merged[key][field] = merged[key][field] or item[field]
        else:
            merged[key] = item
    return list(merged.values())


def upstream_bibtex(paper):
    """Authoritative BibTeX: Crossref when published, arXiv otherwise.

    A record that no source will resolve is reported and skipped rather than
    aborting the run -- upstream profiles do carry the occasional bad ID.
    """
    sources = []
    if paper["doi"]:
        sources.append((f"https://doi.org/{paper['doi']}", "application/x-bibtex"))
    if paper["arxiv"]:
        sources.append((f"https://arxiv.org/bibtex/{paper['arxiv']}", None))
    for url, accept in sources:
        try:
            parsed = parse_bib(fetch(url, accept=accept))
        except (urllib.error.URLError, ValueError) as exc:
            print(f"  WARN     {url} -> {exc}", file=sys.stderr)
            continue
        if parsed:
            return normalize(parsed[0])
    return None


# --------------------------------------------------------------------------
# Merge
# --------------------------------------------------------------------------

STOPWORDS = {"a", "an", "the", "of", "on", "in", "for", "and", "from", "with", "to"}


def make_key(entry, taken):
    author = (entry.get("author") or "unknown").split(" and ")[0]
    surname = (author.split(",")[0] if "," in author else author.split()[-1]).lower()
    surname = re.sub(r"[^a-z]", "", surname) or "unknown"
    year = re.sub(r"[^0-9]", "", entry.get("year") or "")
    words = [w for w in re.findall(r"[a-z]+", (entry.get("title") or "").lower())
             if w not in STOPWORDS]
    base = f"{surname}{year}{''.join(words[:3])}"[:48]
    key, n = base, 2
    while key in taken:
        key, n = f"{base}{n}", n + 1
    return key


MONTHS = {m: m for m in
          ("jan", "feb", "mar", "apr", "may", "jun",
           "jul", "aug", "sep", "oct", "nov", "dec")}


def clean_abstract(text):
    """Collapse whitespace but leave LaTeX alone -- these abstracts are full of it.

    Braces are only escaped when unbalanced, which would otherwise break the
    parser on the next run; balanced ones belong to \\mathrm{...} and friends.
    """
    text = re.sub(r"\s+", " ", (text or "").strip())
    depth = 0
    for char in text:
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                break
    if depth != 0:
        text = text.replace("{", r"\{").replace("}", r"\}")
    return text


def normalize(entry):
    """Repo conventions: bare 3-letter month macros, https DOI links."""
    month = (entry.get("month") or "").strip().lower()
    if month[:3] in MONTHS:
        entry.set("month", month[:3], delim="")
    url = entry.get("url") or ""
    if "doi.org/" in url:
        entry.set("url", "https://doi.org/" + url.split("doi.org/", 1)[1])
    return entry


def build_entry(paper, fetched, taken):
    entry = Entry(fetched.etype, "", dict(fetched.fields), "")
    entry.dirty = True
    entry.fields = {k: v for k, v in entry.fields.items() if k in BIBLIOGRAPHIC}
    if paper["abstract"] and "abstract" not in entry.fields:
        entry.set("abstract", clean_abstract(paper["abstract"]))
    if paper["arxiv"] and not entry.get("eprint"):
        entry.set("arxiv", paper["arxiv"])       # renders the arXiv button
    entry.key = make_key(entry, taken)
    return entry


def upgrade(entry, fetched):
    """Refresh bibliographic fields from upstream; leave curation alone."""
    changed = []
    for name, (value, delim) in fetched.fields.items():
        if name not in BIBLIOGRAPHIC or name in ("note", "keywords", "urldate"):
            continue
        if entry.get(name) != value:
            entry.set(name, value, delim)
            changed.append(name)
    if fetched.etype != entry.etype:
        entry.etype, entry.dirty = fetched.etype, True
        changed.append("type")
    # It is no longer a preprint; drop preprint-only scaffolding.
    for name in ("eprint", "archiveprefix", "primaryclass", "publisher"):
        if name in entry.fields and name not in fetched.fields:
            entry.drop(name)
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would change without writing")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    text = BIB_PATH.read_text()
    entries = parse_bib(text)
    print(f"papers.bib: {len(entries)} entries", file=sys.stderr)

    by_arxiv = {a: e for e in entries if (a := entry_arxiv(e))}
    by_doi = {d: e for e in entries if (d := norm_doi(e.get("doi")))}
    by_title = {norm_title(e.get("title")): e for e in entries}

    papers = discover()
    print(f"upstream:   {len(papers)} papers", file=sys.stderr)

    added, updated, needs_preview = [], [], []
    for paper in sorted(papers, key=lambda p: str(p["year"] or ""), reverse=True):
        match = (by_arxiv.get(paper["arxiv"]) or by_doi.get(paper["doi"])
                 or by_title.get(norm_title(paper["title"])))

        if match is None:
            fetched = upstream_bibtex(paper)
            if fetched is None:
                print(f"  SKIP     no bibtex for {paper['title'][:60]}", file=sys.stderr)
                continue
            taken = {e.key for e in entries} | {e.key for e in added}
            new = build_entry(paper, fetched, taken)
            added.append(new)
            needs_preview.append(new.key)
            print(f"  NEW      {paper['arxiv'] or paper['doi']}  {paper['title'][:58]}")
            continue

        if paper["doi"] and is_preprint(match):
            fetched = upstream_bibtex(paper)
            if fetched is None:
                continue
            changed = upgrade(match, fetched)
            if changed:
                updated.append(match.key)
                venue = match.get("journal") or match.get("booktitle") or paper["doi"]
                print(f"  UPDATED  {match.key}  ->  {venue}")
                if args.verbose:
                    print(f"           fields: {', '.join(sorted(changed))}")

    if not added and not updated:
        print("already in sync")
        return 0

    # Newest first, matching how jekyll-scholar groups the rendered page.
    body = "\n\n".join(e.render() for e in added + entries).strip() + "\n"

    if args.dry_run:
        print("\n--dry-run: papers.bib not written")
    else:
        BIB_PATH.write_text(body)
        print(f"\nwrote {BIB_PATH.relative_to(BIB_PATH.parent.parent)}: "
              f"+{len(added)} new, {len(updated)} upgraded")

    if needs_preview:
        print("\nadd a preview image (assets/img/publication_preview/) and "
              "`preview={...}` to:")
        for key in needs_preview:
            print(f"  - {key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
