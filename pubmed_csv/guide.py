"""The ? window: everything the app can do, on one page.

Kept out of app.py because it is text, not behaviour: the wording changes
whenever a feature does, and that should not mean editing the main window.
"""

import sys
import tkinter as tk
from tkinter import font as tkfont, ttk

from pubmed_csv import assets, widgets

WINDOW_SIZE = (620, 620)
PAD = 12

# The app binds both, so the page may as well name the one that is under the
# reader's own hands.
MODIFIER = "Cmd" if sys.platform == "darwin" else "Ctrl"

SUMMARY = (
    "Search PubMed with several keywords at once, sort the results by hand, "
    "and export them to Excel or CSV — one row per article, with its title, "
    "PMID, DOI and link."
)

# (heading, bullets). What the window says the app does, so it is the list to
# edit when the app learns something new.
SECTIONS = (
    (
        "Building the search",
        (
            "As many keywords as you need, each joined to the ones above it by "
            "AND, OR or NOT.",
            "“+ Add keyword” adds a row, “✕” removes one.",
            "The read-only Query field shows exactly what will be sent to "
            "PubMed, updated as you type.",
            "“Recent searches” keeps the last 20 searches, from one session to "
            "the next. Picking one fills the form back in, ready to adjust.",
            "Enter, from anywhere in the window, runs the search.",
        ),
    ),
    (
        "Running the search",
        (
            "“Limit results to” is off by default: every matching article is "
            "fetched. Tick it to stop earlier.",
            "A progress bar and a live count while the search runs.",
            "“Search” becomes “Stop”. Stopping keeps everything fetched so far "
            "— it can still be exported.",
            "PubMed itself returns at most 9,999 articles per search, whatever "
            "is asked for. The status bar says when a search has hit that.",
        ),
    ),
    (
        "The results table",
        (
            "The title, PMID, DOI and link of every article.",
            "Double-click a row to open the article in your browser.",
            "Drag a column edge to resize it, or use “Fit to content” / "
            "“Reset widths”.",
            "Titles containing italics — gene and species names, which are "
            "everywhere on PubMed — are shown in full.",
        ),
    ),
    (
        "Sorting the rows before exporting",
        (
            "Select rows — Ctrl-click for several, Shift-click for a run — then "
            "“Remove selected”, or the Delete key.",
            "Only the rows still in the table are exported.",
            "“Undo removal”, or Ctrl+Z, takes back the last removal and only "
            "that one, as many times as needed.",
            "“Restore all” brings every removed row back at once.",
        ),
    ),
    (
        "Exporting",
        (
            "“Export…” saves the kept rows. The file type follows the name you "
            "give it.",
            ".xlsx gives a real Excel workbook: clickable links, a bold header "
            "that stays visible while scrolling, columns already sized.",
            ".csv gives a plain CSV that Excel opens with accents intact.",
        ),
    ),
    (
        "Good to know",
        (
            "Each condition applies to the whole query built above it, not just "
            "to its neighbour: three rows give ((A) AND (B)) NOT (C), so a NOT "
            "excludes the term from the entire result.",
            "The app looks for a newer release on startup and offers to open "
            "the download page.",
            "The version in the corner of the window is what a bug report "
            "needs.",
        ),
    ),
)


# (group, ((keys, what it does), …)). "{mod}" becomes Ctrl or Cmd.
SHORTCUTS = (
    (
        "Anywhere in the window",
        (
            ("Enter", "Run the search"),
            ("F1", "Open this window"),
        ),
    ),
    (
        "In the results table",
        (
            ("Double-click", "Open that article in your browser"),
            ("{mod}-click", "Add a row to the selection, or take it out"),
            ("Shift-click", "Select every row between it and the last one"),
            ("{mod}+A", "Select every row"),
            ("Delete", "Remove the selected rows from the export"),
            ("{mod}+Z", "Put back the last rows removed"),
            ("Drag a column edge", "Make that column wider or narrower"),
        ),
    ),
    (
        "In this window",
        (
            ("Esc", "Close it"),
        ),
    ),
)


def open_window(parent: tk.Misc, version: str, repo_url: str) -> tk.Toplevel:
    """Build and show the features window, centred on the main one."""
    window = tk.Toplevel(parent)
    window.title("PubMed Search — Features")
    window.transient(parent.winfo_toplevel())
    window.minsize(*WINDOW_SIZE)

    frame = ttk.Frame(window, padding=PAD)
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(1, weight=1)

    ttk.Label(frame, text=f"PubMed Search v{version}", font=_heading_font(2)).grid(
        row=0, column=0, sticky="w", pady=(0, PAD // 2)
    )

    notebook = ttk.Notebook(frame)
    notebook.grid(row=1, column=0, sticky="nsew")
    notebook.add(_features_page(notebook), text="Features")
    notebook.add(_shortcuts_page(notebook), text="Shortcuts")

    footer = ttk.Frame(frame)
    footer.grid(row=2, column=0, sticky="ew", pady=(PAD, 0))
    footer.columnconfigure(0, weight=1)

    # Held on the window: Tk drops an image nothing else refers to.
    window.github_mark = tk.PhotoImage(
        data=assets.github_mark(float(window.tk.call("tk", "scaling")))
    )
    widgets.link_label(
        footer,
        " Report an issue or suggest a feature on GitHub",
        f"{repo_url}/issues",
        image=window.github_mark,
    ).grid(row=0, column=0, sticky="w")
    ttk.Button(footer, text="Close", command=window.destroy).grid(row=0, column=1)

    window.bind("<Escape>", lambda _event: window.destroy())
    _centre(window, parent.winfo_toplevel())
    window.focus_set()
    return window


def _heading_font(step: int = 1) -> tkfont.Font:
    """The default font, bold, `step` points larger."""
    font = tkfont.nametofont("TkDefaultFont").copy()
    font.configure(size=abs(font.cget("size")) + step, weight="bold")
    return font


def _features_page(parent: ttk.Notebook) -> ttk.Frame:
    """Everything the app does, as running text."""
    page = ttk.Frame(parent, padding=PAD // 2)
    page.columnconfigure(0, weight=1)
    page.rowconfigure(0, weight=1)

    text = tk.Text(page, wrap="word", padx=PAD // 2, pady=PAD // 2, borderwidth=0)
    scrollbar = ttk.Scrollbar(page, orient="vertical", command=text.yview)
    text.configure(yscrollcommand=scrollbar.set)
    text.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    _fill(text)
    text.configure(state="disabled")  # a page to read, not a field to edit
    return page


def _shortcuts_page(parent: ttk.Notebook) -> ttk.Frame:
    """Every key and mouse gesture the app answers to, grouped by where."""
    page = ttk.Frame(parent, padding=PAD)
    page.columnconfigure(1, weight=1)

    row = 0
    for group, shortcuts in SHORTCUTS:
        ttk.Label(page, text=group, font=_heading_font()).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(PAD if row else 0, PAD // 2)
        )
        row += 1
        for keys, description in shortcuts:
            ttk.Label(
                page,
                text=keys.format(mod=MODIFIER),
                font=tkfont.nametofont("TkFixedFont"),
                relief="solid",
                borderwidth=1,
                padding=(6, 1),
                anchor="center",
            ).grid(row=row, column=0, sticky="w", padx=(PAD, PAD), pady=2)
            ttk.Label(page, text=description).grid(row=row, column=1, sticky="w")
            row += 1
    return page


def _fill(text: tk.Text) -> None:
    body = tkfont.nametofont("TkDefaultFont")
    text.tag_configure("summary", font=body, spacing3=PAD, lmargin1=2, lmargin2=2)
    text.tag_configure(
        "heading", font=_heading_font(), spacing1=PAD, spacing3=PAD // 3, lmargin1=2
    )
    # The hanging indent is what keeps a wrapped bullet lined up under its text
    # rather than under its dot.
    text.tag_configure("bullet", font=body, lmargin1=PAD, lmargin2=PAD * 2, spacing3=4)

    text.insert("end", SUMMARY + "\n", "summary")
    for heading, bullets in SECTIONS:
        text.insert("end", heading + "\n", "heading")
        for bullet in bullets:
            text.insert("end", f"•  {bullet}\n", "bullet")


def _centre(window: tk.Toplevel, parent: tk.Misc) -> None:
    """Put the window over the middle of the main one, not the screen."""
    window.update_idletasks()
    width, height = WINDOW_SIZE
    x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - height) // 3
    window.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")
