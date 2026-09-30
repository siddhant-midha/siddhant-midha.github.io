#!/usr/bin/env bash
#
# Refresh the CV PDF published at /assets/pdf/cv.pdf.
#
# The LaTeX source lives in assets/TeX/cv, which is a separate git repository
# (an Overleaf clone) and is gitignored here. Only the built PDF is published,
# and it is copied out so that the nested repository is never added to this one.
#
# Workflow: edit and build in the Overleaf clone, run this, then commit.

set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
src="$root/assets/TeX/cv/main.pdf"
dst="$root/assets/pdf/cv.pdf"

if [[ ! -f "$src" ]]; then
    echo "error: $src not found." >&2
    echo "Build the PDF in the Overleaf clone first (git pull there if needed)." >&2
    exit 1
fi

if cmp -s "$src" "$dst"; then
    echo "assets/pdf/cv.pdf is already up to date."
    exit 0
fi

cp "$src" "$dst"
echo "updated assets/pdf/cv.pdf ($(du -h "$dst" | cut -f1))"
echo
echo "publish it with:"
echo "  git add assets/pdf/cv.pdf && git commit -m 'Update CV' && git push"
