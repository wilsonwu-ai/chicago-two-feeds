"""Chicago address grid -> orientation label.

Chicago numbers addresses outward from State & Madison at 0/0, 800 units per mile.
So the directional number in a street address states, exactly, how far that door is
from the city's centre point. That is a real orientation aid and it is derivable
from the address alone -- no geocoding, no invented data.
"""
import re

UNITS_PER_MILE = 800
DIRS = {"N": "north", "S": "south", "E": "east", "W": "west"}
# The number in an address measures ONE axis, from that axis's baseline --
# Madison St for north/south, State St for east/west. It is not the straight-line
# distance from the centre, and labelling it that way would be wrong.
BASELINE = {"N": "Madison", "S": "Madison", "E": "State", "W": "State"}
_PAT = re.compile(r"^\s*(\d{1,5})\s+([NSEW])\b", re.I)


def grid_label(address: str):
    """Return (block, direction, miles) or None when the address has no grid number."""
    if not address:
        return None
    m = _PAT.match(address.strip())
    if not m:
        return None
    num, d = int(m.group(1)), m.group(2).upper()
    block = (num // 100) * 100
    return block, d, block / UNITS_PER_MILE


def grid_caption(address: str):
    """Human label, exact about which axis is being measured. None when underivable."""
    g = grid_label(address)
    if not g:
        return None
    block, d, miles = g
    return f"{block} {d}", f"{miles:.1f} mi {d} of {BASELINE[d]}"


if __name__ == "__main__":
    cases = [
        ("Cloud Gate",            "201 E Randolph St"),
        ("Au Cheval",             "800 W Randolph St"),
        ("Pequod's",              "2207 N Clybourn Ave"),
        ("Garfield Pk Consv",     "300 N Central Park Ave"),
        ("Shedd Aquarium",        "1200 S Lake Shore Dr"),
        ("Museum of Sci & Ind",   "5700 S Lake Shore Dr"),
        ("Chinatown / Phoenix",   "2131 S Archer Ave"),
        ("no grid number",        "Navy Pier"),
        ("empty",                 ""),
    ]
    for name, addr in cases:
        g = grid_label(addr)
        c = grid_caption(addr)
        out = f"{c[0]:>7s}   {c[1]}" if c else "     --   (no grid number in address)"
        print(f"{name:24s} {addr:28s} -> {out}")
