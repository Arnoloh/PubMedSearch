"""Desktop application to search PubMed and export the results to CSV."""

import queue
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, font as tkfont, messagebox, ttk

from pubmed_csv.export import (
    DEFAULT_MAX_RESULTS,
    FETCH_CEILING,
    SearchOutcome,
    run_search,
    write_csv,
    write_xlsx,
)
from pubmed_csv import history, updates
from pubmed_csv.query import OPERATORS, Term, build_query
from pubmed_csv.version import __version__

WINDOW_TITLE = "PubMed Search"
PAD = 8
POLL_INTERVAL_MS = 100
UPDATE_FIRST_CHECK_MS = 1200  # let the window draw before any update dialog

# Results table columns: (id, heading, starting width, minimum width).
# No column stretches: Tk overrides the width of a stretching column to fill
# the view, which would undo both a drag and a fit. Widths stay exactly where
# they are put, and the horizontal scrollbar covers the overflow.
RESULT_COLUMNS = (
    ("title", "Title", 420, 120),
    ("pmid", "PMID", 90, 60),
    ("doi", "DOI", 180, 80),
    ("url", "Link", 240, 100),
)
COLUMN_TEXT_MARGIN = 24  # breathing room around the widest cell when auto-fitting
COLUMN_FIT_MAX_WIDTH = 700  # keeps a long title from pushing the other columns off


class KeywordRow:
    """One keyword field, with the operator joining it to the row above it."""

    def __init__(self, parent: ttk.Frame, on_change, on_remove):
        self.keyword = tk.StringVar()
        self.operator = tk.StringVar(value="AND")

        self.lead_label = ttk.Label(parent, text="Keyword")
        self.operator_box = ttk.Combobox(
            parent,
            textvariable=self.operator,
            values=list(OPERATORS),
            state="readonly",
            width=6,
        )
        self.entry = ttk.Entry(parent, textvariable=self.keyword)
        self.remove_button = ttk.Button(
            parent, text="✕", width=3, command=lambda: on_remove(self)
        )

        self.keyword.trace_add("write", lambda *_: on_change())
        self.operator.trace_add("write", lambda *_: on_change())

    def place(self, row: int, is_first: bool, removable: bool) -> None:
        """Lay the widgets out; the first row shows no operator."""
        if is_first:
            self.operator_box.grid_remove()
            self.lead_label.grid(row=row, column=0, sticky="w", padx=(0, PAD), pady=3)
        else:
            self.lead_label.grid_remove()
            self.operator_box.grid(row=row, column=0, sticky="w", padx=(0, PAD), pady=3)

        self.entry.grid(row=row, column=1, sticky="ew", pady=3)

        if removable:
            self.remove_button.grid(row=row, column=2, sticky="w", padx=(PAD, 0), pady=3)
        else:
            self.remove_button.grid_remove()

    def destroy(self) -> None:
        for widget in (self.lead_label, self.operator_box, self.entry, self.remove_button):
            widget.destroy()

    def term(self) -> Term:
        return Term(keyword=self.keyword.get(), operator=self.operator.get())


class PubMedApp(ttk.Frame):
    """Main window: keywords in, results table and CSV export out."""

    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=PAD * 2)
        master.title(WINDOW_TITLE)

        self.rows: list[KeywordRow] = []
        self.articles: list = []
        self.results_queue: queue.Queue = queue.Queue()
        self.searching = False
        self.cancel_event = threading.Event()

        self.query_preview = tk.StringVar()
        # Unticked by default: a search returns everything it matches unless
        # asked otherwise. The count stays at 100, ready for when it is ticked.
        self.limit_results = tk.BooleanVar(value=False)
        self.max_results = tk.StringVar(value=str(DEFAULT_MAX_RESULTS))
        self.limit_hint = tk.StringVar()
        self.status = tk.StringVar(value="Enter one or more keywords, then run the search.")

        self.searches = history.load_searches()

        self._build_ui()
        self._refresh_history()
        self._add_row()
        self._add_row()
        master.bind("<Return>", lambda _event: self._start_search())
        self.rows[0].entry.focus_set()
        self._start_update_check()

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)  # the results table takes the free space

        self._build_keywords_section()
        self._build_query_preview()
        self._build_options_section()
        self._build_actions()
        self._build_results_table()
        self._build_status_bar()

    def _build_keywords_section(self) -> None:
        frame = ttk.LabelFrame(self, text="Search terms", padding=PAD)
        frame.grid(row=0, column=0, sticky="ew")
        frame.columnconfigure(1, weight=1)

        self.keywords_frame = ttk.Frame(frame)
        self.keywords_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.keywords_frame.columnconfigure(1, weight=1)

        actions = ttk.Frame(frame)
        actions.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(PAD, 0))
        actions.columnconfigure(1, weight=1)

        ttk.Button(actions, text="+ Add keyword", command=self._add_row).grid(
            row=0, column=0, sticky="w"
        )

        ttk.Label(actions, text="Recent searches").grid(
            row=0, column=2, sticky="e", padx=(PAD, PAD // 2)
        )
        self.history_box = ttk.Combobox(actions, state="readonly", width=48)
        self.history_box.grid(row=0, column=3, sticky="e")
        self.history_box.bind("<<ComboboxSelected>>", self._restore_search)

    def _build_query_preview(self) -> None:
        frame = ttk.Frame(self)
        frame.grid(row=1, column=0, sticky="ew", pady=(PAD, 0))
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Query").grid(row=0, column=0, sticky="w", padx=(0, PAD))
        ttk.Entry(frame, textvariable=self.query_preview, state="readonly").grid(
            row=0, column=1, sticky="ew"
        )

    def _build_options_section(self) -> None:
        frame = ttk.Frame(self)
        frame.grid(row=2, column=0, sticky="ew", pady=(PAD, 0))

        ttk.Checkbutton(
            frame,
            text="Limit results to",
            variable=self.limit_results,
            command=self._on_limit_toggled,
        ).grid(row=0, column=0, sticky="w", padx=(0, PAD))

        self.max_results_spinbox = ttk.Spinbox(
            frame,
            from_=1,
            to=FETCH_CEILING,
            textvariable=self.max_results,
            width=7,
        )
        self.max_results_spinbox.grid(row=0, column=1, sticky="w")

        ttk.Label(frame, textvariable=self.limit_hint).grid(
            row=0, column=2, sticky="w", padx=(PAD, 0)
        )
        self._on_limit_toggled()

    def _on_limit_toggled(self) -> None:
        """Grey out the count when the search is meant to return everything."""
        if self.limit_results.get():
            self.max_results_spinbox.configure(state="normal")
            self.limit_hint.set("articles.")
        else:
            self.max_results_spinbox.configure(state="disabled")
            self.limit_hint.set(
                f"— off: every match is fetched, up to PubMed's {FETCH_CEILING:,} limit."
            )

    def _build_actions(self) -> None:
        frame = ttk.Frame(self)
        frame.grid(row=3, column=0, sticky="ew", pady=(PAD * 2, PAD))
        frame.columnconfigure(2, weight=1)

        self.search_button = ttk.Button(
            frame, text="Search", command=self._on_search_button
        )
        self.search_button.grid(row=0, column=0, sticky="w")

        self.export_button = ttk.Button(
            frame, text="Export…", command=self._export, state="disabled"
        )
        self.export_button.grid(row=0, column=1, sticky="w", padx=(PAD, 0))

        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.grid(row=0, column=2, sticky="ew", padx=(PAD * 2, 0))

    def _build_results_table(self) -> None:
        frame = ttk.Frame(self)
        frame.grid(row=4, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(frame)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, PAD // 2))
        toolbar.columnconfigure(0, weight=1)
        ttk.Label(
            toolbar,
            text="Drag a column edge to resize it.",
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(toolbar, text="Fit to content", command=self._fit_columns).grid(
            row=0, column=1, sticky="e"
        )
        ttk.Button(toolbar, text="Reset widths", command=self._reset_columns).grid(
            row=0, column=2, sticky="e", padx=(PAD // 2, 0)
        )

        self.tree = ttk.Treeview(
            frame,
            columns=[column for column, *_ in RESULT_COLUMNS],
            show="headings",
            selectmode="browse",
        )
        for column, heading, width, minwidth in RESULT_COLUMNS:
            self.tree.heading(column, text=heading)
            self.tree.column(
                column, width=width, minwidth=minwidth, stretch=False, anchor="w"
            )

        vertical = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        vertical.grid(row=1, column=1, sticky="ns")
        horizontal.grid(row=2, column=0, sticky="ew")
        self.tree.bind("<Double-1>", self._open_selected)

    # ---------------------------------------------------- column widths

    def _fit_columns(self) -> None:
        """Widen each column to the longest value it currently shows."""
        cell_font = tkfont.nametofont("TkDefaultFont")
        for column, heading, _width, minwidth in RESULT_COLUMNS:
            widest = cell_font.measure(heading)
            for item in self.tree.get_children():
                widest = max(widest, cell_font.measure(self.tree.set(item, column)))
            self.tree.column(
                column,
                width=max(minwidth, min(widest + COLUMN_TEXT_MARGIN, COLUMN_FIT_MAX_WIDTH)),
            )

    def _reset_columns(self) -> None:
        """Put every column back to its starting width."""
        for column, _heading, width, _minwidth in RESULT_COLUMNS:
            self.tree.column(column, width=width)

    def _build_status_bar(self) -> None:
        ttk.Label(self, textvariable=self.status, anchor="w").grid(
            row=5, column=0, sticky="ew", pady=(PAD, 0)
        )

    # ------------------------------------------------------- keyword rows

    def _add_row(self) -> None:
        row = KeywordRow(self.keywords_frame, self._refresh_query, self._remove_row)
        self.rows.append(row)
        self._refresh_rows()
        row.entry.focus_set()

    def _remove_row(self, row: KeywordRow) -> None:
        if len(self.rows) == 1:
            return
        self.rows.remove(row)
        row.destroy()
        self._refresh_rows()

    def _refresh_rows(self) -> None:
        """Re-place every row so the operators follow the current order."""
        removable = len(self.rows) > 1
        for index, row in enumerate(self.rows):
            row.place(row=index, is_first=index == 0, removable=removable)
        self._refresh_query()

    def _refresh_query(self) -> None:
        self.query_preview.set(build_query(row.term() for row in self.rows))

    def _set_terms(self, terms: list[Term]) -> None:
        """Replace the form's rows with a stored search."""
        for row in self.rows:
            row.destroy()
        self.rows = []

        for term in terms:
            row = KeywordRow(self.keywords_frame, self._refresh_query, self._remove_row)
            row.keyword.set(term.keyword)
            row.operator.set(term.operator)
            self.rows.append(row)

        if not self.rows:  # never leave the form with nothing to type into
            self.rows.append(
                KeywordRow(self.keywords_frame, self._refresh_query, self._remove_row)
            )
        self._refresh_rows()

    # ----------------------------------------------------------- history

    def _refresh_history(self) -> None:
        self.history_box.configure(values=[build_query(t) for t in self.searches])

    def _restore_search(self, _event=None) -> None:
        index = self.history_box.current()
        if 0 <= index < len(self.searches):
            self._set_terms(self.searches[index])
            self.status.set("Search restored. Adjust it or press Search.")

    def _record_search(self, terms: list[Term]) -> None:
        self.searches = history.remember(self.searches, terms)
        history.save_searches(self.searches)
        self._refresh_history()

    # ------------------------------------------------------------ search

    def _on_search_button(self) -> None:
        """The one button starts a search, and stops the running one."""
        if self.searching:
            self.cancel_event.set()
            self.status.set("Stopping…")
        else:
            self._start_search()

    def _start_search(self) -> None:
        if self.searching:  # the Return key can fire while one is running
            return

        terms = [row.term() for row in self.rows]
        query = build_query(terms)
        if not query:
            messagebox.showwarning("No keywords", "Enter at least one keyword to search.")
            return

        max_results = self._requested_max_results()
        if max_results is False:  # invalid entry, already reported
            return

        self._record_search(terms)
        self.cancel_event.clear()
        self._set_searching(True)
        self.status.set(f"Searching PubMed for {query} …")
        thread = threading.Thread(
            target=self._search_worker,
            args=(query, max_results),
            daemon=True,
        )
        thread.start()
        self.after(POLL_INTERVAL_MS, self._poll_results)

    def _requested_max_results(self) -> int | None | bool:
        """The cap to apply: a number, None for no cap, False if unusable."""
        if not self.limit_results.get():
            return None

        try:
            max_results = int(self.max_results.get())
        except ValueError:
            messagebox.showwarning("Invalid number", "Max results must be a whole number.")
            return False
        if not 1 <= max_results <= FETCH_CEILING:
            messagebox.showwarning(
                "Invalid number",
                f"Max results must be between 1 and {FETCH_CEILING:,}.",
            )
            return False
        return max_results

    def _search_worker(self, query: str, max_results: int | None) -> None:
        """Run the search off the UI thread and hand the result back by queue."""
        try:
            outcome = run_search(
                query,
                max_results=max_results,
                progress=lambda fetched, total: self.results_queue.put(
                    ("progress", (fetched, total))
                ),
                is_cancelled=self.cancel_event.is_set,
            )
        except Exception as error:  # network, API and parsing failures alike
            self.results_queue.put(("error", error))
        else:
            self.results_queue.put(("ok", outcome))

    def _poll_results(self) -> None:
        try:
            kind, payload = self.results_queue.get_nowait()
        except queue.Empty:
            self.after(POLL_INTERVAL_MS, self._poll_results)
            return

        if kind == "progress":
            self._show_progress(*payload)
            self.after(POLL_INTERVAL_MS, self._poll_results)
            return

        self._set_searching(False)
        if kind == "error":
            self.status.set("Search failed.")
            messagebox.showerror("Search failed", str(payload) or type(payload).__name__)
        else:
            self._show_results(payload)

    def _show_progress(self, fetched: int, total: int) -> None:
        """Swap the spinner for a real bar once the batch count is known."""
        if self.progress["mode"] != "determinate":
            self.progress.stop()
            self.progress.configure(mode="determinate", maximum=total)
        self.progress.configure(value=fetched)
        if not self.cancel_event.is_set():
            self.status.set(f"Fetching articles… {fetched:,} of {total:,}")

    def _show_results(self, outcome: SearchOutcome) -> None:
        self.articles = outcome.articles
        self.tree.delete(*self.tree.get_children())
        for article in self.articles:
            self.tree.insert(
                "",
                "end",
                values=(article.title, article.pmid, article.doi or "", article.url),
            )

        self.export_button.configure(state="normal" if self.articles else "disabled")
        self.status.set(self._result_summary(outcome))

    def _result_summary(self, outcome: SearchOutcome) -> str:
        retrieved = len(outcome.articles)
        total = outcome.total_matches

        if outcome.cancelled:
            if not retrieved:
                return f"Stopped. This query matches {total:,} articles."
            return f"Stopped after {retrieved:,} of {total:,} articles. Export still works."
        if not retrieved:
            return "No article found for this query."

        tail = " Double-click a row to open it."
        if retrieved == total:
            return f"Retrieved all {total:,} matching articles.{tail}"
        if outcome.capped_by_api:
            return (
                f"Retrieved {retrieved:,} of {total:,} matching articles — PubMed "
                f"returns at most {FETCH_CEILING:,} per search.{tail}"
            )
        return f"Retrieved {retrieved:,} of {total:,} matching articles.{tail}"

    def _set_searching(self, searching: bool) -> None:
        self.searching = searching
        self.search_button.configure(text="Stop" if searching else "Search")
        if searching:
            self.progress.configure(mode="indeterminate")
            self.progress.start(12)
        else:
            self.progress.stop()
            self.progress.configure(mode="indeterminate", value=0)

    # ------------------------------------------------------------ export

    def _export(self) -> None:
        """Save the results, as Excel or CSV depending on the chosen name."""
        if not self.articles:
            return

        path = filedialog.asksaveasfilename(
            title="Save results",
            defaultextension=".xlsx",
            initialfile="pubmed_results.xlsx",
            filetypes=[
                ("Excel workbook", "*.xlsx"),
                ("CSV file", "*.csv"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        write = write_csv if path.lower().endswith(".csv") else write_xlsx
        try:
            write(self.articles, path)
        except OSError as error:
            messagebox.showerror("Export failed", str(error))
            return

        self.status.set(f"Saved {len(self.articles):,} articles to {path}")

    def _open_selected(self, _event=None) -> None:
        selection = self.tree.selection()
        if selection:
            webbrowser.open(self.tree.set(selection[0], "url"))

    # ------------------------------------------------------ update check

    def _start_update_check(self) -> None:
        """Ask GitHub for a newer release, off the UI thread."""
        self.update_queue: queue.Queue = queue.Queue()
        threading.Thread(target=self._update_worker, daemon=True).start()
        self.after(UPDATE_FIRST_CHECK_MS, self._poll_update)

    def _update_worker(self) -> None:
        # check_for_update swallows its own failures; guard anyway so a
        # surprise here can never take the app down on startup.
        try:
            self.update_queue.put(updates.check_for_update(__version__))
        except Exception:
            self.update_queue.put(None)

    def _poll_update(self) -> None:
        try:
            release = self.update_queue.get_nowait()
        except queue.Empty:
            self.after(POLL_INTERVAL_MS * 5, self._poll_update)
            return

        if release is not None:
            self._offer_update(release)

    def _offer_update(self, release: updates.Release) -> None:
        wants_it = messagebox.askyesno(
            "Update available",
            f"Version {release.version} is available.\n"
            f"You are running {__version__}.\n\n"
            "Open the download page?",
        )
        if wants_it:
            webbrowser.open(release.url)


def main() -> None:
    root = tk.Tk()
    app = PubMedApp(root)
    app.pack(fill="both", expand=True)
    root.minsize(820, 600)
    root.lift()
    root.focus_force()
    root.mainloop()


if __name__ == "__main__":
    main()
