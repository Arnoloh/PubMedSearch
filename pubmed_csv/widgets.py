"""Small widgets used by more than one window."""

import tkinter as tk
import webbrowser
from tkinter import font as tkfont, ttk

MUTED_COLOUR = "grey"  # present, but never the thing the eye lands on
LINK_COLOUR = "#0969DA"  # GitHub's own link blue, under the pointer


class CircleButton(tk.Canvas):
    """A round button, which no ttk theme offers.

    Drawn rather than themed: an oval and a character on a canvas, so the
    circle comes out the same on Windows and macOS. Only the background is
    borrowed from the theme, so it still sits invisibly on its parent in both
    light and dark.
    """

    MARGIN = 8  # how much wider than the character the circle sits

    def __init__(self, parent: tk.Misc, text: str, command, colour: str = MUTED_COLOUR):
        font = tkfont.nametofont("TkDefaultFont")
        size = font.metrics("linespace") + self.MARGIN
        super().__init__(
            parent,
            width=size,
            height=size,
            highlightthickness=0,
            borderwidth=0,
            background=ttk.Style().lookup("TFrame", "background"),
            cursor="hand2",
        )
        self.command = command
        self.colour = colour

        self._circle = self.create_oval(1, 1, size - 1, size - 1, outline=colour)
        self._text = self.create_text(
            size / 2 + 1, size / 2, text=text, fill=colour, font=font
        )

        self.bind("<Enter>", lambda _event: self._paint(LINK_COLOUR))
        self.bind("<Leave>", lambda _event: self._paint(self.colour))
        self.bind("<ButtonRelease-1>", lambda _event: self.invoke())

    def invoke(self) -> None:
        """Run the command, as a ttk.Button of the same name would."""
        self.command()

    def _paint(self, colour: str) -> None:
        self.itemconfigure(self._circle, outline=colour)
        self.itemconfigure(self._text, fill=colour)


def link_label(
    parent: tk.Misc,
    text: str,
    url: str,
    image: tk.PhotoImage | None = None,
    colour: str = MUTED_COLOUR,
) -> ttk.Label:
    """A label that opens `url` when clicked, and says so on hover."""
    label = ttk.Label(parent, text=text, foreground=colour, cursor="hand2")
    if image is not None:
        label.configure(image=image, compound="left")

    label.bind("<Button-1>", lambda _event: webbrowser.open(url))
    label.bind("<Enter>", lambda _event: label.configure(foreground=LINK_COLOUR))
    label.bind("<Leave>", lambda _event: label.configure(foreground=colour))
    return label
