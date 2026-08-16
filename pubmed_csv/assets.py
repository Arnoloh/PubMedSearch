"""Images the UI draws, embedded as base64 PNG.

A one-file build carries no folder of assets next to the .exe, and reading a
file from beside a frozen executable is exactly what does not work there. Tk
loads a PhotoImage straight from base64, so the picture lives in the source.

The GitHub mark below is GitHub's own icon, downsampled and recoloured to the
grey the status bar uses. It marks a link to this project's repository, which
is what GitHub's logo guidelines allow the mark to be used for.
"""


def github_mark(scaling: float) -> str:
    """The mark at the size that suits the display.

    ``tk scaling`` is points per pixel: 1.0 on a normal display, ~1.5 or more
    on a Windows machine set to 150% and up, where a 16px image would look
    shrunken beside text the toolkit has already scaled up.
    """
    return _MARK_32 if scaling > 1.5 else _MARK_16


_MARK_16 = """
    iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAABHklEQVR42mPIK2tkpAQzYBFk
    B+JYIF4NxBeB+AoQbwbiHCDmJ2SAORDfAuL/OPBLIPbHZYAtEH/FoxmG/0JdiGKAABA/hSrw
    BuJkIN4PxAuAeB4Q7wPiMiDWhRrwDYjVkA2oRrJBE0+gsQHxL6i6RcgGXIQK3gdibjwGMAHx
    AajazyADQQawAvFvqOBEIqIuC8m1GgxQG2ECE0g0wIgB6qz3UIHTRBiwBMkASVgYbEASrIAa
    ik1zGJJ3ryMHojs0DRQC8QtoYopF0ugCxOfR0kMeekJaDsR3gdgXGvemSHK6aJpPQqMUxQAu
    IN4OxOeAuBeI9ZHk1JE0XwD5HVdeYAHifCB+BsQ+SOKqQPwBiFvR0wkDjsBiwRKQrNjUAgDI
    mbyslSlQhgAAAABJRU5ErkJggg==
"""

_MARK_32 = """
    iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAACZUlEQVR42mPIK2tkHEjMMBQd
    oALEyUDcB8RLgHgFEM8E4nIgtgdiNlo4QAyIK4D4MhD/J4DfA/F8ILag1AEwOZBv36JZ8o8I
    h4DULAdiAXIdwAfEq/FY/A+Pxcj0UyB2INUBgkB8nghfEou/AbErsQ5gBeJdVLQchr8CsRUx
    DmhH07gOiJ2AeCIQfybSsgNAHAXEiWjid4CYE58DjIH4D5qmaCR5GSCeBMTNQBwLxJ7QoA0G
    4kIgng3E7kjqQZb9RDNvAj4HrMbiG1cKCxv0HATyoBI2B0gB8Q8sDsikwHIhtBD9B8VN2BxQ
    jCV7gYLPkAIHsAPxKSyeuoTNAbuxKJxBhfJeH4j/ooXAH2jpCncAE1JcIYeAB5UqnStYCi53
    ZAfw4SjZ1KnkgM1YzE5DdoAEjiKWWg7YgsUBRcgOEMRRoNhTyQFnsJidhewAZiD+gkVRIRUs
    54TWBehm+6PnguNYFB2HJlBKHJCOo8ZUQHdAC45ooKQgkgPid2hZEMR+gK0c0ILm139Yis5y
    Upta0JrvGg5PTcFVFxyEKrgOxDpAvApJ02NoEWoHxPxYLGQBYl1o9tpLoNVkissB3kgaD0MN
    XIwlRAywOACUkHcSUVVvINQeWIukuAdalB5Bq+txBXs8EQ1WKUIOEESKu7fQ1ApqijsCcTgQ
    m+BxgDuBRmoksW1CUAn4BinuA4CYG5oQRfA4wA2P5cWktopVgfgCkiF/ofG/isQQALUxMsjt
    mPAA8Syk6hSE1+BR74Fm+VVC7Qlie0bm0E4GqGW7AI86O2hwn4NmR05q9w15gZiDiG7c0Okd
    AwBGjPLcD6ttlgAAAABJRU5ErkJggg==
"""
