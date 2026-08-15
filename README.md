# PubMed Search → CSV

A small desktop application (Tkinter, no browser involved) to search PubMed
with several keywords combined by `AND` / `OR` / `NOT`, and export the results
to a CSV holding the **title**, **PMID**, **DOI** and **link** of each article.

Built on [pypubmed](https://github.com/lescientifik/pypubmed).

## Run

```bash
.venv/bin/python -m pubmed_csv
```

## Install elsewhere

Tkinter is required. On macOS with Homebrew Python it ships separately:

```bash
brew install python-tk@3.14        # matches your Python minor version
pip install -e .                   # pulls pypubmed from GitHub
pubmed-csv                         # or: python -m pubmed_csv
```

## Building a standalone executable

[PubMedSearch.spec](PubMedSearch.spec) drives a [PyInstaller](https://pyinstaller.org)
build into one self-contained file — no Python needed on the machine that runs it.

**PyInstaller cannot cross-compile.** A Windows `.exe` must be built on Windows,
a macOS binary on macOS. Building on your Mac produces a Mac binary, not an exe.

### Windows .exe without a Windows machine (GitHub Actions)

[.github/workflows/build-windows.yml](.github/workflows/build-windows.yml) builds
it on a Windows runner, for free:

```bash
git init && git add -A && git commit -m "PubMed search app"
gh repo create pubmed-csv --private --source=. --push
```

Then open the repo's **Actions** tab → **Build Windows executable** → **Run
workflow**. When the job turns green, `PubMedSearch-windows` is downloadable
from the run's summary page, containing `PubMedSearch.exe`.

Pushing a tag publishes the exe as a release instead:

```bash
git tag v1.0.0 && git push origin v1.0.0
```

### On a Windows machine

With [Python for Windows](https://www.python.org/downloads/windows/) installed
(tick *Add python.exe to PATH*; its Tkinter is included):

```bat
pip install . pyinstaller
pyinstaller PubMedSearch.spec
```

`dist\PubMedSearch.exe` is the result — one file, copy it anywhere.

### On this Mac

```bash
.venv/bin/pip install pyinstaller
.venv/bin/pyinstaller PubMedSearch.spec   # -> dist/PubMedSearch
```

### With Docker (Wine)

Plain Docker cannot do it: Linux containers build Linux binaries, and Windows
containers need a Windows kernel, so they do not run on macOS at all. What does
work is **Wine** inside a Linux container, running Windows Python and
PyInstaller — [build-windows-docker.sh](build-windows-docker.sh) wraps that:

```bash
./build-windows-docker.sh     # -> dist/PubMedSearch.exe
```

**This does not work on Apple Silicon.** Tried on an M5: Wine aborts inside its
own memory setup before reaching any project code.

```
wine: dlls/ntdll/unix/virtual.c:267: anon_mmap_fixed:
      Assertion `!((UINT_PTR)start & host_page_mask)' failed.
qemu: uncaught target signal 6 (Aborted)
```

Wine needs an x86_64 CPU and the image is `linux/amd64` only. Rosetta does not
rescue it — Rosetta cannot run 32-bit x86, which Wine's startup helpers use, so
they fall back to QEMU, and Wine's `ntdll` reserves memory at fixed low
addresses that QEMU's address space cannot satisfy. No image or flag works
around that.

Use this script on an **x86_64 Linux** host, where nothing is emulated. On
Apple Silicon, build through GitHub Actions or a Windows VM instead. Test the
exe on real Windows either way — Wine is a compatibility layer, not Windows.

### Things to expect

- **Windows SmartScreen** will warn the first time the exe runs, because it is
  unsigned: *More info → Run anyway*. Silencing it for good needs a paid code
  signing certificate.
- **Antivirus false positives** happen with single-file PyInstaller builds. The
  spec leaves UPX compression off, which reduces them.
- **First launch takes a second or two**: a one-file build unpacks itself into a
  temporary folder. Swap `EXE(...)` for a `COLLECT(...)` build if you would
  rather have a fast-starting folder than a single file.
- The exe is roughly **15 MB** and needs no Python on the target machine.

## Using the app

1. Type a keyword in the first field.
2. Press **+ Add keyword** for each extra keyword, and pick the operator
   (`AND`, `OR`, `NOT`) that joins it to everything above it.
3. The **Query** box shows the exact PubMed query being sent, live.
4. Set **Limit results to** (see below).
5. Press **Search** (or hit Return), then **Export CSV…** to save the file.

Double-click any row in the results table to open the article in your browser.

### How many results

**Limit results to** is **unticked by default**, so a search returns every
article the query matches. Tick it to cap the count — it starts at **100** and
is adjustable at any time.

PubMed hands back at most **9,999 articles per search**, so that is where an
unticked search stops; the status line says so when it happens. Narrow the
query with another condition to get under the ceiling.

Large searches are fetched 200 articles at a time, with a progress bar and a
running count. The **Search** button becomes **Stop** while one is running —
stopping keeps whatever has already been fetched, and you can still export it.

### Column widths

Drag any column edge in the results table to resize it. Widths stay exactly
where you put them, and a horizontal scrollbar appears if the columns together
grow wider than the window. Two buttons sit above the table:

- **Fit to content** — sizes every column to its longest value, so nothing is
  cut off. Titles stop at 700 px, otherwise one long title would push the other
  columns out of view.
- **Reset widths** — back to the starting widths.

Column widths affect the table only; the CSV is unchanged.

### Operators

Each condition applies to the **whole query above it**, not just to the line
before it. The query so far is bracketed, then the new operator and keyword are
appended, so conditions stack the way you read them down the form:

| Keyword | Operator | Resulting query |
|---------|----------|-----------------|
| CRISPR  | —        | `(CRISPR)` |
| cancer  | AND      | `(CRISPR) AND (cancer)` |
| mice    | NOT      | `((CRISPR) AND (cancer)) NOT (mice)` |
| CAR-T   | OR       | `(((CRISPR) AND (cancer)) NOT (mice)) OR (CAR-T)` |

This is what makes complex searches behave. PubMed reads a flat query strictly
left to right, so `a AND b OR c` would return everything matching `c` on its
own; the nesting states the grouping outright.

The first keyword has no operator, since PubMed operators are binary. Blank
fields are skipped, so a half-filled form still searches, and a blank row in
the middle adds no bracket. Full PubMed syntax works inside a field too, e.g.
`smith j[Author]` or `(cancer OR tumour)`.

### CSV output

UTF-8 with a BOM, so Excel opens accented titles correctly.

```csv
title,pmid,doi,url
Polyamines buffer labile iron...,42600612,10.1016/j.cell.2026.07.040,https://pubmed.ncbi.nlm.nih.gov/42600612/
```

Articles with no DOI registered in PubMed get an empty `doi` cell.

Titles are re-read from the PubMed XML so that inline markup survives. pypubmed
parses titles in a way that stops at the first tag, which blanks a title such as
`<i>NF2</i> loss transforms …` and truncates `Role of <i>TP53</i> in cancer`
down to `Role of`. Since gene and species names are italicised throughout
PubMed, [export.py](pubmed_csv/export.py) reads those titles again from the same
response, with no extra requests.

## Layout

| File | Purpose |
|------|---------|
| [pubmed_csv/query.py](pubmed_csv/query.py) | Builds the boolean query from the keyword rows |
| [pubmed_csv/export.py](pubmed_csv/export.py) | Runs the search, writes the 4-column CSV |
| [pubmed_csv/app.py](pubmed_csv/app.py) | Tkinter window |

Searches run on a background thread, so the window stays responsive.

## Tests

```bash
.venv/bin/python -m unittest discover -s tests
```
# yanis
# yanis
