"""KV[Cr(CN)6], a Prussian-blue cage of vanadium and chromium joined by cyanide, first made in 1999: V(II) and Cr(III) spins oppose and cancel, and it stays magnetically ordered up to 376 K.

The DFT-relaxed conventional cell (PBE+U, U = 3 eV), F-43m with K ordered on half the tetrahedral holes, and its moments, ±2.12 μB, from the compensated-magnet ledger
(github.com/spicylemonade/compensated-magnet-ledger @ 45551de, materials/*/structures), copied beside this file.
The calculation has no spin-orbit coupling, so the arrows lie along cubic [111], off every bond.
"""
from pathlib import Path

import crystal

HERE = Path(__file__).resolve().parent


def scene():
    return crystal.scene(HERE / "KVCrCN6_F-43m_conv_PBEU110_relaxed.cif", HERE / "KVCrCN6_prim15_LCM.mcif", (1, 1, 1), 3.2), 0.0, {}
