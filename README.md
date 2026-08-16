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
it on a Windows runner, for free. Open the repo's **Actions** tab → **Build
Windows executable** → **Run workflow**; when the job turns green, the
`PubMedSearch` artifact on the run's summary page contains `PubMedSearch.exe`.

### macOS and Linux builds

One workflow per target, each runnable on its own from the **Actions** tab:

| Workflow | Runner | Artifact |
|---|---|---|
| [build-windows.yml](.github/workflows/build-windows.yml) | `windows-latest` | `PubMedSearch.exe` |
| [build-macos.yml](.github/workflows/build-macos.yml) | `macos-latest` (arm64) | `PubMedSearch-macos-arm64.zip` |
| [build-linux.yml](.github/workflows/build-linux.yml) | `ubuntu-24.04` (x86_64) | `PubMedSearch-linux-amd64.tar.gz` |

The macOS build produces a real `PubMedSearch.app`, so it opens from Finder
instead of launching a Terminal window, and it is zipped with `ditto` to keep
the bundle's permissions and ad-hoc signature — a plain artifact upload strips
those and leaves an app that refuses to open. The Linux binary is tarred for
the same reason: a bare upload loses the executable bit.

Each build asserts `uname -m` matches the architecture its artifact name
promises, so it fails loudly rather than shipping an arm64 binary labelled
amd64 if a runner label is ever repointed. The Linux build installs
`python3-tk` first: without the Tcl/Tk runtime beside it, PyInstaller happily
bundles an app that dies on launch with no window.

Being unsigned, the macOS app is not notarised — Gatekeeper blocks it on first
open, and the way past is right-click → *Open* rather than a double-click.

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

### Not with Docker, on this Mac

Worth recording, since it looks like it should work. Plain Docker cannot build
an exe — Linux containers build Linux binaries, and Windows containers need a
Windows kernel. Running Windows Python under **Wine** in a Linux container can,
but not on Apple Silicon: Wine aborts inside its own memory setup, before
reaching any project code.

```
wine: dlls/ntdll/unix/virtual.c:267: anon_mmap_fixed:
      Assertion `!((UINT_PTR)start & host_page_mask)' failed.
qemu: uncaught target signal 6 (Aborted)
```

Wine needs an x86_64 CPU, and Rosetta does not rescue it: Rosetta cannot run
32-bit x86, which Wine's startup helpers use, so they fall back to QEMU — and
Wine's `ntdll` reserves memory at fixed low addresses that QEMU's address space
cannot satisfy. No image or flag works around that. Use GitHub Actions.

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

### Update check

On every launch the app asks GitHub whether a newer release exists, and offers
to open the download page if so. The check runs on a background thread, so it
never delays startup, and it stays silent whenever the answer is not a clear
yes — offline, no releases yet, rate limited, or already up to date. Nothing to
configure and nothing to dismiss in the normal case.

It needs the repo to be public, which it is: a distributed app carries no
credentials, and a private repo would answer 404 and leave the check silently
doing nothing.

## Releasing a new version

The tag is the only thing to set. There is no version to bump by hand:

```bash
git tag v1.1.0 && git push origin master --tags
```

That starts [.github/workflows/release.yml](.github/workflows/release.yml),
which does the whole thing in order:

| Job | What it does |
|---|---|
| `verify` | Rejects a tag that is not a stampable version, in seconds |
| `windows` | Calls [build-windows.yml](.github/workflows/build-windows.yml) |
| `macos` | Calls [build-macos.yml](.github/workflows/build-macos.yml) |
| `linux` | Calls [build-linux.yml](.github/workflows/build-linux.yml) |
| `release` | Publishes, **only if all three builds succeeded** |

Each build runs [stamp_version.py](stamp_version.py) before compiling, which
rewrites the `__version__` line in
[pubmed_csv/version.py](pubmed_csv/version.py) to the tag — so tagging `v1.1.0`
produces builds reporting `1.1.0`, and the update check stops offering an
update the moment you are running the latest tag. `pyproject.toml` reads that
same file, so the packaged version follows too. The value committed in
`version.py` is only what a local, untagged build reports.

Tags must be numeric (`v1.1.0`, `v2.0`); anything else, `v1.2.0-rc1` included,
is refused by `verify` rather than producing a build with a bogus version.

The builds publish nothing themselves — they only produce artifacts, so a
half-finished release cannot appear when one platform fails. The release job
also refuses to publish unless all three files are present, rather than
shipping a release quietly missing a platform.

Versions compare as dotted numbers, so `v1.10.0` correctly ranks after `v1.2.0`,
and drafts and prereleases are ignored.

### Recent searches

Every search you run is remembered. The **Recent searches** dropdown, next to
*+ Add keyword*, refills the whole form when you pick one — keywords and
operators both — so you can re-run it or tweak it instead of retyping it.

The history keeps the **last 20** searches, newest first. Re-running an old one
moves it back to the top rather than duplicating it, and blank rows are dropped
before it is stored. It persists between launches, in:

| | |
|---|---|
| Windows | `%APPDATA%\PubMedSearch\history.json` |
| macOS | `~/Library/Application Support/PubMedSearch/history.json` |
| Linux | `~/.config/PubMedSearch/history.json` |

Deleting that file clears the history. If it is missing or damaged the app
starts with an empty history rather than complaining.

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

### Output: Excel or CSV

**Export…** saves either format — the choice is the file name. Anything ending
in `.csv` is written as CSV; everything else becomes an Excel workbook, which is
what the dialog offers first.

Both hold the same four columns: `title`, `pmid`, `doi`, `url`.

**Excel (.xlsx)** is the better default: no encoding or separator guessing when
Excel opens it, links are clickable, the header row is bold and frozen, and the
columns arrive already sized (titles capped so one long one cannot swallow the
sheet).

**CSV** is UTF-8 with a BOM, so Excel still reads accented titles correctly.

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
| [pubmed_csv/history.py](pubmed_csv/history.py) | Stores and reloads recent searches |
| [pubmed_csv/updates.py](pubmed_csv/updates.py) | Checks GitHub for a newer release |
| [pubmed_csv/export.py](pubmed_csv/export.py) | Runs the search, writes the Excel and CSV files |
| [pubmed_csv/app.py](pubmed_csv/app.py) | Tkinter window |

Searches run on a background thread, so the window stays responsive.
