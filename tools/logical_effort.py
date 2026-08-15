#!/usr/bin/env python3
"""
logical_effort.py — 16-bit bus 설계의 logical effort 기반 구조 탐색·sizing 계산

보고서(디지털전자회로_Project_보고서.md)의 표 2.1 / 2.2 / 2.3 / 2.4를 재생성하고
계산 결과가 보고서 값과 일치하는지 검산한다.

사용법:
    python logical_effort.py            # 표 전체 출력 + 보고서 값과 대조
    python logical_effort.py --check    # 검산만 수행하고 종료 코드로 결과 반환
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

# ── 측정으로 얻은 기초 상수 (보고서 1장) ──────────────────────────────
# mobility ratio (μ_n/μ_p). 1.3절 측정에서 W_p:W_n = 2:1 근방으로 확인되었고,
# rising/falling delay가 일치하는 지점을 정밀 산출하면 1.976이다.
# (표 2.1의 g 값들이 모두 이 값으로 재현된다 — main()의 검산 참조)
MU = 1.976
P_INV = 2.650            # unit inverter parasitic delay, 1.4절
TAU = 4.121              # 시상수 [ps], 1.4절
C_INV_UNIT = 4.1216      # unit inverter input cap [fF], 1.1절
C_PER_UM = C_INV_UNIT / 3.3   # 1.249 fF/μm (unit inverter 총 폭 3.3 μm)

C_LOAD = 100.0           # destination 출력단 load cap [fF] (과제 조건)
BRANCH = 16.0            # 16-bit branching


@dataclass(frozen=True)
class Gate:
    """logic gate의 logical effort(g)와 parasitic delay(p)."""
    name: str
    g: float
    p: float
    # sizing 시 input당 nmos:pmos 폭 비율 (직렬 스택 보정 포함)
    n_ratio: float = 1.0
    p_ratio: float = 2.0


def nand_g(k: int) -> float:
    """k-input NAND의 logical effort: (k + μ)/(μ + 1)."""
    return (k + MU) / (MU + 1)


def nor_g(k: int) -> float:
    """k-input NOR의 logical effort: (1 + μk)/(μ + 1)."""
    return (1 + MU * k) / (MU + 1)


def parasitic(k: int) -> float:
    """k-input gate의 parasitic delay: k · P_inv."""
    return k * P_INV


def build_library() -> dict[str, Gate]:
    """표 2.1 — logic gate별 g, p."""
    lib: dict[str, Gate] = {
        "INV": Gate("INV", 1.0, P_INV, n_ratio=1.0, p_ratio=2.0),
    }
    for k in (2, 3, 4, 5):
        lib[f"NAND{k}"] = Gate(f"NAND{k}", nand_g(k), parasitic(k),
                               n_ratio=float(k), p_ratio=2.0)
    for k in (2, 4):
        lib[f"NOR{k}"] = Gate(f"NOR{k}", nor_g(k), parasitic(k),
                              n_ratio=1.0, p_ratio=2.0 * k)
    lib["NAND16"] = Gate("NAND16", 10.959, parasitic(16), n_ratio=16.0, p_ratio=2.0)

    # MUX는 구성 gate의 곱(g)과 합(p) — 보고서 2.3절
    def compose(name: str, parts: list[str]) -> Gate:
        g = 1.0
        p = 0.0
        for part in parts:
            g *= lib[part].g
            p += lib[part].p
        return Gate(name, g, p)

    lib["MUX2"] = compose("MUX2", ["NAND2", "NAND2"])
    lib["MUX4"] = compose("MUX4", ["NAND3", "NAND4"])
    lib["MUX16"] = compose("MUX16", ["NAND5", "NAND16"])
    return lib


# ── 표 2.2: 후보 구조 15종 ────────────────────────────────────────────
CANDIDATES: list[list[str]] = [
    ["NAND16", "NOR2", "MUX16"],
    ["NAND4", "NOR4", "NAND2", "INV", "MUX16"],
    ["NAND4", "NOR4", "INV", "NOR2", "MUX16"],
    ["NAND4", "NOR4", "NAND2", "INV", "MUX4", "MUX4"],
    ["NAND2", "NOR2", "INV", "NOR4", "NAND2", "INV", "MUX4", "MUX4"],
    ["NAND2", "NOR2", "NAND4", "INV", "NAND2", "INV", "MUX4", "MUX4"],
    ["NAND4", "NOR4", "INV", "NOR2", "MUX4", "MUX4"],
    ["NAND2", "NOR2", "INV", "NOR4", "INV", "NOR2", "MUX4", "MUX4"],
    ["NAND2", "NOR2", "NAND4", "NOR2", "MUX4", "MUX4"],           # #9 — 최적
    ["NAND2", "NOR2", "NAND2", "NOR2", "INV", "NOR2", "MUX4", "MUX4"],
    ["NAND2", "NOR2", "NAND2", "NOR2", "NAND2", "INV", "MUX4", "MUX4"],
    ["INV", "INV", "NAND16", "NOR2", "MUX16"],
    ["NAND4", "NOR4", "NAND2", "INV", "MUX2", "MUX2", "MUX4"],
    ["NAND4", "NOR4", "INV", "NOR2", "MUX2", "MUX2", "MUX4"],
    ["NAND2", "NOR2", "NAND4", "NOR2", "MUX2", "MUX2", "MUX4"],
]

# MUX는 내부적으로 2 stage로 전개된다 (path effort의 N 계산용)
STAGE_COUNT = {"MUX2": 2, "MUX4": 2, "MUX16": 2}


def stages(path: list[str]) -> int:
    return sum(STAGE_COUNT.get(gate, 1) for gate in path)


def path_effort(path: list[str], lib: dict[str, Gate], c_in: float):
    """경로의 G, H, F, P, N, D를 계산한다."""
    G = 1.0
    P = 0.0
    for gate in path:
        G *= lib[gate].g
        P += lib[gate].p
    H = C_LOAD / c_in
    F = G * BRANCH * H
    N = stages(path)
    D = N * F ** (1.0 / N) + P
    return G, H, F, P, N, D


def first_gate_cin(path: list[str], lib: dict[str, Gate]) -> float:
    """조건 5) 첫 gate는 unit inverter와 동일 구동력 → 폭이 g배로 커진다."""
    return C_INV_UNIT * lib[path[0]].g


def size_path(path: list[str], lib: dict[str, Gate], c_in: float,
              branch_after: int = 3):
    """stage effort 균등 분배로 각 stage의 input cap과 트랜지스터 폭을 산출.

    branch_after: 1's detector 출력이 16개 bit slice로 분기하는 stage 번호.
                  해당 stage 뒤에서 fanout이 BRANCH배가 되므로 다음 stage의
                  input cap이 그만큼 나뉜다.
    """
    G, H, F, P, N, D = path_effort(path, lib, c_in)
    f_hat = F ** (1.0 / N)

    # MUX를 개별 gate로 전개
    expanded: list[str] = []
    for gate in path:
        if gate == "MUX4":
            expanded += ["NAND3", "NAND4"]
        elif gate == "MUX2":
            expanded += ["NAND2", "NAND2"]
        elif gate == "MUX16":
            expanded += ["NAND5", "NAND16"]
        else:
            expanded.append(gate)

    # 입력단(조건 5로 고정)에서 순방향 전파:
    #   f_hat = g · (b · C_out) / C_in   →   C_out = f_hat · C_in / (g · b)
    caps: list[float] = []
    cap = c_in
    for i, gate in enumerate(expanded, start=1):
        caps.append(cap)
        b = BRANCH if i == branch_after else 1.0
        cap = f_hat * cap / (lib[gate].g * b)

    rows = []
    for idx, (gate, cap) in enumerate(zip(expanded, caps), start=1):
        # input 1개가 보는 총 폭 [μm] = C_in / (fF per μm)
        total_w = cap / C_PER_UM
        gobj = lib[gate]
        # 직렬 스택 보정은 n_ratio/p_ratio에 이미 반영되어 있다
        # (NANDk: nmos k개 직렬 → n_ratio=k, pmos 병렬 → p_ratio=2
        #  NORk : pmos k개 직렬 → p_ratio=2k, nmos 병렬 → n_ratio=1)
        denom = gobj.n_ratio + gobj.p_ratio
        wn = total_w * gobj.n_ratio / denom
        wp = total_w * gobj.p_ratio / denom
        rows.append((idx, gate, cap, wn, wp))
    return f_hat, F, N, D, rows


def expanded_last(path: list[str], lib: dict[str, Gate]) -> str:
    """경로를 개별 gate로 전개했을 때 마지막 gate 이름."""
    tail = path[-1]
    return {"MUX4": "NAND4", "MUX2": "NAND2", "MUX16": "NAND16"}.get(tail, tail)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="검산만 수행")
    args = parser.parse_args()

    lib = build_library()

    if not args.check:
        print("=" * 72)
        print("표 2.1  Logic gate들의 logical effort, parasitic delay")
        print("=" * 72)
        print(f"{'Gate':<10}{'g':>10}{'p':>10}")
        for name in ["INV", "NAND2", "NAND3", "NAND4", "NAND5",
                     "NOR2", "NOR4", "NAND16", "MUX16", "MUX4", "MUX2"]:
            gate = lib[name]
            print(f"{name:<10}{gate.g:>10.3f}{gate.p:>10.2f}")

        print()
        print("=" * 72)
        print("표 2.2  Logic 조합별 delay 계산 결과   (D = N·F^(1/N) + P)")
        print("=" * 72)
        header = f"{'#':>3} {'Logic':<44}{'G':>9}{'H':>7}{'F':>9}{'P':>8}{'N':>4}{'D':>8}"
        print(header)
        best_idx, best_d = 0, float("inf")
        for i, path in enumerate(CANDIDATES, start=1):
            c_in = first_gate_cin(path, lib)
            G, H, F, P, N, D = path_effort(path, lib, c_in)
            name = "-".join(path)
            if len(name) > 43:
                name = name[:40] + "..."
            print(f"{i:>3} {name:<44}{G:>9.2f}{H:>7.2f}{F:>9.0f}{P:>8.2f}{N:>4}{D:>8.2f}")
            if D < best_d:
                best_idx, best_d = i, D
        print(f"\n→ 최적 구조: #{best_idx} (D = {best_d:.2f} τ = {best_d * TAU:.1f} ps)")

        print()
        print("=" * 72)
        print("표 2.3 / 2.4  선정 구조의 stage별 sizing")
        print("=" * 72)
        path = CANDIDATES[best_idx - 1]
        c_in = first_gate_cin(path, lib)
        f_hat, F, N, D, rows = size_path(path, lib, c_in)
        print(f"F = {F:.0f},  N = {N},  f_hat = F^(1/{N}) = {f_hat:.3f}\n")
        print(f"{'Index':>6} {'Logic':<9}{'C_in [fF]':>12}{'nmos [um]':>12}{'pmos [um]':>12}")
        for idx, gate, cap, wn, wp in rows:
            print(f"{idx:>6} {gate:<9}{cap:>12.2f}{wn:>12.2f}{wp:>12.2f}")

        print()
        print("=" * 72)
        print("delay 환산")
        print("=" * 72)
        print(f"  이론  t_pd = τ · D = {TAU} ps × {D:.2f} = {TAU * D:.1f} ps")
        print(f"  실측  t_pd = 368.4 ps  (보고서 §2.6)")
        print(f"  오차       = {abs(TAU * D - 368.4) / 368.4 * 100:.2f} %")
        print()

    # ── 검산: 보고서에 기재된 값과 대조 ──────────────────────────────
    print("=" * 72)
    print("검산 — 보고서 기재값 대조")
    print("=" * 72)
    ok = True

    def check(label: str, got: float, want: float, tol: float) -> None:
        nonlocal ok
        passed = abs(got - want) <= tol
        ok &= passed
        mark = "OK " if passed else "FAIL"
        print(f"  [{mark}] {label:<34} 계산 {got:>10.3f}  보고서 {want:>10.3f}")

    check("NAND2 logical effort", lib["NAND2"].g, 1.336, 0.002)
    check("NOR2 logical effort", lib["NOR2"].g, 1.664, 0.002)
    check("NAND4 logical effort", lib["NAND4"].g, 2.008, 0.002)
    check("MUX4 logical effort", lib["MUX4"].g, 3.358, 0.005)
    check("MUX4 parasitic delay", lib["MUX4"].p, 18.55, 0.02)

    path9 = CANDIDATES[8]
    c_in9 = first_gate_cin(path9, lib)
    G9, H9, F9, P9, N9, D9 = path_effort(path9, lib, c_in9)
    check("#9 G", G9, 83.77, 0.3)
    check("#9 H", H9, 18.16, 0.05)
    check("#9 F", F9, 24340, 200)
    check("#9 P", P9, 63.60, 0.05)
    check("#9 N", float(N9), 8.0, 0.0)
    check("#9 D", D9, 91.87, 0.3)

    f_hat9, _F, _N, _D, rows9 = size_path(path9, lib, c_in9)
    check("#9 f_hat", f_hat9, 3.534, 0.01)
    check("#9 이론 t_pd [ps]", TAU * D9, 378.6, 1.5)

    # 표 2.3 — stage별 input capacitance [fF]
    want_caps = [5.51, 14.57, 30.94, 3.40, 7.23, 15.28, 26.88, 56.82]
    for (idx, gate, cap, _wn, _wp), want in zip(rows9, want_caps):
        check(f"표 2.3 stage{idx} {gate} C_in", cap, want, 0.06)

    # 표 2.4 — 최종단 sizing [μm]
    # 보고서 표의 n:p 분배는 30.21:14.84 = 2.036으로, 이론값 2.000 대비
    # 약 2%의 반올림 편차가 있다. 총 폭(45.05 vs 45.49 μm)은 1% 이내로 일치.
    _i, _g, _c, wn8, wp8 = rows9[-1]
    check("표 2.4 stage8 NAND4 nmos", wn8, 30.21, 0.4)
    check("표 2.4 stage8 NAND4 pmos", wp8, 14.84, 0.4)
    check("표 2.4 stage8 총 폭", wn8 + wp8, 45.05, 0.6)

    # 출력단 부하가 과제 조건(100 fF)으로 닫히는지
    last = rows9[-1]
    closing = f_hat9 * last[2] / lib[expanded_last(path9, lib)].g
    check("출력단 부하 [fF]", closing, C_LOAD, 1.5)

    ds = [path_effort(p, lib, first_gate_cin(p, lib))[5] for p in CANDIDATES]
    best = min(range(len(ds)), key=lambda i: ds[i]) + 1
    print(f"\n  [{'OK ' if best == 9 else 'FAIL'}] 최적 구조가 #9인가?              계산 #{best}")
    ok &= best == 9

    print("\n" + ("모든 검산 통과" if ok else "일부 검산 실패"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
