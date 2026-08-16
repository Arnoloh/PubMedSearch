*Lire en [français](README.fr.md).*

# PubMed Search

A small desktop application to search [PubMed](https://pubmed.ncbi.nlm.nih.gov/)
with several keywords combined by `AND` / `OR` / `NOT`, and export the results to
Excel or CSV - one row per article, with its **title**, **PMID**, **DOI** and **link**.

It was written for a friend working on a kinesiology thesis: he had hundreds of
articles to go through and needed the same four fields for every one of them.
Doing it by hand, one article at a time, was the tedious part - this does it in
one pass.

## Contents

- [Install](#install)
- [Features](#features)
- [How to use it](#how-to-use-it)
- [Good to know](#good-to-know)
- [Feedback and contributions](#feedback-and-contributions)
- [TODO](#todo)

## Install

Download `PubMedSearch.exe` from the
[latest release](https://github.com/Arnoloh/PubMedSearch/releases/latest) and run it.
Nothing to set up: it is a single file, and it works on Windows.

The app checks for a newer version when it starts, and offers to open the
download page if there is one. Its version number is shown in the bottom-right
corner of the window.

## Features

**Building the search**

- As many keywords as you need, each joined to the ones above it by `AND`, `OR`
  or `NOT`.
- `+ Add keyword` adds a row, `✕` removes one.
- A read-only `Query` field shows exactly what will be sent to PubMed, updated as
  you type.
- `Recent searches` keeps the last 20 searches, saved between sessions. Picking
  one refills the form so you can tweak it and run it again.
- Press `Enter` anywhere in the window to launch the search.

**Running the search**

- `Limit results to` is off by default, so every matching article is fetched.
  Tick it to stop earlier.
- A progress bar and a live count (`Fetching articles… 400 of 1,200`) while the
  search runs.
- The `Search` button becomes `Stop`. Stopping keeps everything already fetched -
  you can still export it.
- The status bar says how many articles matched and how many were retrieved.

**The results**

- A table with the **title**, **PMID**, **DOI** and **link** of every article.
- Double-click a row to open the article in your browser.
- Drag a column edge to resize it, or use `Fit to content` / `Reset widths`.
- Titles containing italics - gene and species names, which are everywhere on
  PubMed - are shown in full rather than cut off at the first italicised word.

**Exporting**

- `Export…` saves the results. The file type follows the name you give it.
- `.xlsx` gives a real Excel workbook: clickable links, bold header that stays
  visible while scrolling, columns already sized.
- `.csv` gives a plain CSV that Excel opens with accents intact.

## How to use it

1. **Type your keywords.** One per row, choosing `AND`, `OR` or `NOT` for each
   row after the first.
2. **Check the query.** The `Query` field shows what will be sent to PubMed, so
   nothing is guessed on your behalf.
3. **Search.** Press `Search` or hit `Enter`.
4. **Export.** Press `Export…` and give the file a name ending in `.xlsx` or
   `.csv`.

## Good to know

Each condition applies to the whole query built above it, not just to its
neighbour: three rows give `((A) AND (B)) NOT (C)`, so a `NOT` excludes the term
from the entire result rather than from the last keyword only.

PubMed itself returns at most **9,999** articles per search, whatever you ask
for. That is the real ceiling on any search, and the status bar tells you when a
search has hit it.

## Feedback and contributions

Feedback of any kind is welcome, and you do not need to be a developer to give
it. If something is unclear, missing, or simply does not behave the way you
expected, say so - that is exactly what shapes the next version. The same goes
for ideas: a field you wish were exported, a step you wish were quicker.

The simplest way is to open an
[issue](https://github.com/Arnoloh/PubMedSearch/issues) on GitHub, describing what
you did and what you expected. Contributions to the code are just as welcome.

# TODO
- [ ] Filter rows before export (export only the relevant ones)
- [ ] Compile for macos and linux