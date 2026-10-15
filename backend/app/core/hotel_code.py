"""Hotel IDs (DECISIONS D82): `DYN-` and 13 Crockford base32 characters with at least one
letter (13 digits could be mistaken for a card number), e.g. DYN-7K3M9QX2FHT4W.

The database generates them (app.new_hotel_code). People type them on tablets, so input is
forgiving: any case, spaces and dashes ignored, the `DYN` prefix optional, and the letters
Crockford reads as digits (O as 0; I and L as 1) accepted.
"""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import AfterValidator, StringConstraints

ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
PREFIX = "DYN-"
LENGTH = 13
_BODY = re.compile(rf"^[{ALPHABET}]{{{LENGTH}}}$")
_READ_AS = str.maketrans({"O": "0", "I": "1", "L": "1"})


def normalise(raw: str) -> str | None:
    """The canonical Hotel ID for what someone typed, or None if it cannot be one."""
    s = re.sub(r"[\s\-_.]", "", raw).upper()
    if s.startswith("DYN") and len(s) == len("DYN") + LENGTH:
        s = s[3:]
    s = s.translate(_READ_AS)
    return PREFIX + s if _BODY.match(s) else None


def _check(raw: str) -> str:
    code = normalise(raw)
    if code is None:
        raise ValueError("A Hotel ID looks like DYN-7K3M9QX2FHT4W: DYN- and 13 letters and numbers.")
    return code


HotelCode = Annotated[str, StringConstraints(max_length=40), AfterValidator(_check)]
