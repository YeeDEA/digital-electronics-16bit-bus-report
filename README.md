# 16-bit Bus Design in 45nm CMOS

**A comparator-gated 16-bit bus (1's detector + 16:1 MUX) sized entirely by logical effort — hand analysis predicted the SPICE result to within 2.77%.**

![verify](https://github.com/YeeDEA/cmos-16bit-bus-design/actions/workflows/verify.yml/badge.svg)

The system compares two 16-bit words, drives `a` onto the bus only when every bit matches, sends it 200 µm across the die, and selects one line at the far end with a 16:1 multiplexer into a 100 fF load. The design question is whether a closed-form delay model is accurate enough to size a real path without iterating in simulation. I measured the process constants directly (gate capacitance, drain capacitance, τ, p_inv), enumerated 15 candidate gate topologies, picked the one with minimum path effort, sized every stage by equalizing stage effort, then verified in SPICE. Hand analysis predicted 378.6 ps for the logic path against a measured 368.4 ps — **2.77% error** — and the same methodology carried through interconnect modeling, repeater insertion, and crosstalk analysis.

**Conditions:** 45 nm bulk CMOS, V_DD = 1.1 V, 25 °C · unit inverter W_n/W_p = 1.1/2.2 µm · bus l = 200 µm, R_w = 100 Ω/µm, C_w = 0.2 fF/µm, C_adj = 0.3 fF/µm · output load 100 fF.

---

## Results

| Design stage | Measured t_pd | Predicted t_pd | Error |
|---|---|---|---|
| Logic path only (interconnect ignored) | 368.4 ps | 378.6 ps | **2.77%** |
| + unrepeated 200 µm wire | 1030.5 ps | 977.1 ps | 5.2% |
| + repeaters (N = 4) | 762.2 ps | 668.2 ps | 14.1%* |
| + final re-optimization | **756.4 ps** | — | final |

\* Relative to the predicted delay; on the measured basis used by the other rows it is 12.3%. See [Known inconsistencies](#known-inconsistencies-in-the-report).

Supporting results:

- **Repeater sweep** — N = 3/4/5 evaluated; N = 4 is the minimum at 762.2 ps (N = 5: 767.6 ps), a **~270 ps improvement** over the unrepeated wire. Delay is flat near the optimum in both model and simulation, as theory predicts.
- **Crosstalk** — three Miller-effect cases (adjacent line switching in phase / quiet / switching out of phase) measure 409.9 / 795.4 / 2216 ps, a delay ratio of **1 : 1.94 : 5.41** against the coupling-capacitance ratio of 1 : 3 : 5.
- **Interconnect dominance** — one 200 µm wire inflates the path from 378.6 ps to 977.1 ps (2.6×), and wire plus repeaters account for ~75% of total switched capacitance in the power estimate.

---

## Key finding: the theoretically optimal MUX was the slower one

Path-effort math said the destination MUX should be built from **NAND5**, since fewer, wider stages minimized the computed path delay. In simulation that structure measured **763.2 ps — 1.0 ps worse than the unoptimized design it was supposed to beat.**

The reason is the five-transistor series stack. Logical effort captures the added input capacitance of a wide stack but not the body effect, internal node charging, and slew degradation that accumulate through five series devices, so the model was systematically optimistic exactly where it mattered. Rebuilding the MUX from **NAND3/NAND4** and re-sizing recovered the loss and improved on the baseline: **756.4 ps**, with the gain coming entirely from the falling path. Reordering the critical input `c` to the transistor closest to the output in each series stack contributed further.

**Takeaway:** logical effort is an excellent first-order sizing tool (2.77% on the logic path), but its accuracy degrades predictably with stack depth and interconnect. Knowing where the model breaks is what makes it usable.

---

## What this demonstrates

- **Delay modeling and sizing** — logical effort, electrical effort, branching effort, path effort, parasitic delay; sizing a full path by equalizing stage effort and closing exactly on a specified 100 fF load.
- **Interconnect-aware design** — pi-model wire representation, Elmore delay, effective-resistance extraction for driver and repeater, repeater insertion and count optimization.
- **Signal integrity** — coupling capacitance and the Miller effect quantified across three switching scenarios; worst-case crosstalk shown to be a 5.4× delay penalty, with shielding and bus-invert coding identified as mitigations.
- **Design-space exploration** — 15 topologies evaluated analytically before a single transistor was drawn, reducing simulation to a verification step rather than a search.
- **Correlating hand analysis with simulation** — every predicted number carries a measured counterpart and a stated error, with the sources of divergence explained rather than hidden.
- **Checking the RTL against an independent model** — `verif/tb_bus.sv` compares the behavioral RTL with a bit-serial reference model over 21,632 directed and random vectors in CI (a deliberately broken 1's detector is caught on the first single-bit mismatch).
- **Building verification tooling** — the design math is reimplemented as dependency-free Python that regenerates the report tables, self-checks 26 published values, and runs 22 regression tests in CI.

---

## Repository structure

```
├── 디지털전자회로_Project_보고서.{md,pdf,docx}   Full technical report (Korean): device characterization →
│                                              topology selection → wire → repeaters → crosstalk → power
├── 시뮬레이션_재현_가이드.{md,pdf,docx}          Reproduction guide (Korean)
├── docs/
│   ├── reproduce.md         Reproduction guide in English: Cadence Virtuoso/Spectre and ngspice paths
│   └── README.ko.md         Previous Korean README
├── rtl/                     Behavioral SystemVerilog of the bus (source, destination, top)
├── verif/                   Independent bit-serial reference model + self-checking testbench
├── tools/                   Design calculations in Python (no dependencies)
│   ├── logical_effort.py    Topology search, path effort, stage sizing, value self-check
│   ├── wire_analysis.py     Elmore delay, repeater-count sweep, crosstalk cases
│   └── test_design.py       22 regression tests over the design math
├── sim/                     ngspice testbenches
│   ├── lib_gates.sp             Gate library with the final transistor widths
│   ├── tb0a_gatecap.cir         Gate capacitance by slope matching
│   ├── tb0b_draincap.cir        Drain capacitance extraction
│   ├── tb0d_fo_delay.cir        FO1/FO4 delay → τ, p_inv
│   ├── tb1_source_dest_path.cir 8-stage critical path
│   ├── tb2_logic_check.cir      Functional check (XNOR → 1's detector → MUX)
│   ├── tb3_wire_nonrepeated.cir Unrepeated wire, 3-segment pi model
│   ├── tb4_wire_repeated_n4.cir Repeated wire, N = 4
│   ├── tb5_crosstalk.cir        Crosstalk, three Miller cases
│   └── tb6_full_link.cir        Full source → wire → destination link
└── .github/workflows/verify.yml
```

---

## Reproduce the results

**Design calculations** (Python 3.9+, zero dependencies):

```bash
python tools/logical_effort.py   # regenerates the design tables, self-checks 26 report values
python tools/wire_analysis.py    # Elmore delay, optimal repeater count, crosstalk
python tools/test_design.py      # 22 regression tests
```

`logical_effort.py` computes path effort for all 15 candidate topologies from scratch, reproduces the sizing tables, and verifies that the per-stage capacitances close exactly on the 100 fF load.

**SPICE** (ngspice + the free PTM 45 nm model from <https://ptm.asu.edu>):

```bash
cd sim
# download the 45nm_HP model card and save it here as 45nm_HP.pm
ngspice -b tb0d_fo_delay.cir
ngspice -b tb4_wire_repeated_n4.cir
```

The original work used a university PDK under Cadence Virtuoso/Spectre. PTM is a different process, so absolute values differ — **the trends reproduce, not the numbers**. Expected outcomes per testbench are listed in the reproduction guide.

---

## Design methodology

1. **Measure the process constants.** Nothing is taken from a datasheet. Gate capacitance is extracted by sweeping an ideal capacitor against a MOSFET gate load until the output slopes match: **C_inv(unit) = 4.1216 fF** (3.3 µm total width → 1.249 fF/µm). Drain capacitance is extracted the same way with the signal driven into the drain: **C_d,n = 0.5930 fF**, **C_d,p = 1.405 fF**. A PN ratio sweep confirms rise/fall symmetry at W_p:W_n = 2:1 (µ = 2). FO1/FO4 delays of 15.04 ps and 27.40 ps solve to **τ = 4.121 ps** and **p_inv = 2.650**, which convert every normalized delay in the design to picoseconds.

2. **Enumerate topologies and compute path effort.** Logical effort and parasitic delay are tabulated for INV, NAND2–NAND5, NOR2, NOR4, NAND16, and MUX2/MUX4/MUX16 built from NAND stages. Fifteen candidate structures implementing the same function are then compared on B, G, H, F = GBH, P, N, and normalized delay $$D = N \cdot F^{1/N} + P$$

3. **Pick the minimum.** **NAND2-NOR2-NAND4-NOR2-MUX4-MUX4** wins at **D = 91.87τ**, expanding to **8 stages** (the two MUX4 blocks are NAND3 → NAND4 each). Runners-up land at 93.38 and 93.56, so the choice is deliberate rather than marginal — and the naive NAND16-NOR2-MUX16 structure is 62% slower at D = 148.75τ.

4. **Size by equalizing stage effort.** With $$\hat{f} = F^{1/8} = 24340^{1/8} = 3.534$$ each stage's input capacitance follows from $$C_{in} = g \cdot C_{out} / \hat{f}$$ working backward from the 100 fF load. Capacitances convert to widths via the measured 1.249 fF/µm and split into nMOS/pMOS by each gate's stack ratio.

5. **Verify in SPICE.** Transient simulation of the full 8-stage path, rising and falling, five measurements each, averaged: 368.4 ps against 378.6 ps predicted. Functional correctness is checked separately against the truth table.

6. **Add interconnect and iterate.** The wire is modeled as a pi network with Elmore delay, repeater count is swept, and source and destination are re-optimized against the new load conditions — which is where the NAND5 result above surfaced.

---

## Known inconsistencies in the report

Found on re-reading the report after publication. The numbers are left exactly as the report states them; this section says how to read them.

| Where | What the report says | How to read it |
|---|---|---|
| Results table, error column | 2.77% and 5.2% are relative to the **measured** delay; 14.1% (repeaters, N = 4) is relative to the **predicted** 668.2 ps | On the measured basis used by the other rows it is **12.3%** ((762.2 − 668.2) / 762.2) |
| Repeater analysis | N = 4 wire delay is 289.578 ps in the text but 286.7 ps in the table and in `tools/wire_analysis.py` | The tool value (286.7 ps) is the one the rest of the analysis uses |
| Optimal repeater count | Theory's minimum is **N = 5** (283.5 ps); simulation's minimum is **N = 4** (762.2 vs 767.6 ps at N = 5) | Both curves are flat near the optimum, so the model and the simulation disagree on which neighbor wins by only a few ps |
| Crosstalk | Ground capacitance of the observed segment taken as ≈ 30 fF, while the whole wire is C_w·l = 40 fF | The 1 : 3 : 5 coupling ratio depends on that choice; the measured 1 : 1.94 : 5.41 does not |
| Power | ≈ 44 µW is an estimate from an assumed activity factor α ≈ 0.5 | No simulated power number is reported; treat it as an estimate |

## Documents

| File | Contents |
|---|---|
| [디지털전자회로_Project_보고서.md](디지털전자회로_Project_보고서.md) | Full report (Korean) — device characterization, topology selection, sizing, interconnect, repeaters, crosstalk, power estimation |
| [docs/reproduce.md](docs/reproduce.md) | Step-by-step reproduction on Cadence Virtuoso/Spectre or ngspice + PTM |

Independent project, modeled on the project assignment of the Digital Electronic Circuits course (School of Electrical and Electronic Engineering, Yonsei University).
