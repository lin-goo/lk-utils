"""Base58 encoding

Implementations of Base58 and Base58Check endcodings that are compatible
with the bitcoin network.
"""
# This module is based upon base58 snippets found scattered over many bitcoin
# tools written in python. From what I gather the original source is from a
# forum post by Gavin Andresen, so direct your praise to him.
# This module adds shiny packaging and support for python3.
from hashlib import sha256

__version__ = "0.2.5"

# 58 character alphabet used
alphabet = b"a1KztEBZndx3YuyfG6brokj9JDSLCQVw8XvpPNch7qW5AHFmgRT2M4isUe"


if bytes == str:  # python2
    iseq, bseq, buffer = (
        lambda s: map(ord, s),
        lambda s: "".join(map(chr, s)),
        lambda s: s,
    )
else:  # python3
    iseq, bseq, buffer = (
        lambda s: s,
        bytes,
        lambda s: s.buffer,
    )


def scrub_input(v):
    if isinstance(v, str) and not isinstance(v, bytes):
        v = v.encode("ascii")

    if not isinstance(v, bytes):
        raise TypeError(
            "a bytes-like object is required (also str), not '%s'" % type(v).__name__
        )

    return v


def b58encode_int(i, default_one=True):
    """Encode an integer using Base58"""
    if not i and default_one:
        return alphabet[0:1]
    string = b""
    while i:
        i, idx = divmod(i, 58)
        string = alphabet[idx: idx + 1] + string
    return string


def b58encode(v):
    """Encode a string using Base58"""

    v = scrub_input(v)

    nPad = len(v)
    v = v.lstrip(b"\0")
    nPad -= len(v)

    p, acc = 1, 0
    for c in iseq(reversed(v)):
        acc += p * c
        p = p << 8

    result = b58encode_int(acc, default_one=False)

    return alphabet[0:1] * nPad + result


def b58decode_int(v):
    """Decode a Base58 encoded string as an integer"""

    v = scrub_input(v)

    decimal = 0
    for char in v:
        decimal = decimal * 58 + alphabet.index(char)
    return decimal


def b58decode(v):
    """Decode a Base58 encoded string"""

    v = scrub_input(v)

    origlen = len(v)
    v = v.lstrip(alphabet[0:1])
    newlen = len(v)

    acc = b58decode_int(v)

    result = []
    while acc > 0:
        acc, mod = divmod(acc, 256)
        result.append(mod)

    return b"\0" * (origlen - newlen) + bseq(reversed(result))


def b58encode_check(v):
    """Encode a string using Base58 with a 4 character checksum"""

    digest = sha256(sha256(v).digest()).digest()
    return b58encode(v + digest[:4])


def b58decode_check(v):
    """Decode and verify the checksum of a Base58 encoded string"""

    result = b58decode(v)
    result, check = result[:-4], result[-4:]
    digest = sha256(sha256(result).digest()).digest()

    if check != digest[:4]:
        raise ValueError("Invalid checksum")

    return result
