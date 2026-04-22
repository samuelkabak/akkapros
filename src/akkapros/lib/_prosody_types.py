from __future__ import annotations

from enum import Enum


class AccentStyle(Enum):
    LOB = "lob"
    SOB = "sob"


class MoraMode(Enum):
    BI = "bi"
    MONO = "mono"


class SyllableType(Enum):
    CV = 1
    V = 1
    CVC = 2
    VC = 2
    CVV = 2
    VV = 2
    CVVC = 3
    VVC = 3