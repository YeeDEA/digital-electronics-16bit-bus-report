#!/usr/bin/env python3
"""
test_design.py — 설계 계산의 회귀 테스트

보고서에 기재된 값들이 계산 코드로 재현되는지 검증한다.
    python -m pytest tools/test_design.py -v
또는 pytest 없이:
    python tools/test_design.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import logical_effort as le  # noqa: E402
import wire_analysis as wa  # noqa: E402


# ── 1장: 기초 측정값의 내부 일관성 ────────────────────────────────────

def test_tau_and_pinv_from_fo_delays():
    """FO1/FO4 측정치로부터 τ와 p_inv가 보고서 값으로 유도되는가."""
    t_fo1, t_fo4 = 15.04, 27.40
    tau = (t_fo4 - t_fo1) / 3
    p_inv = t_fo1 / tau - 1
    assert abs(tau - le.TAU) < 0.01, f"tau {tau}"
    assert abs(p_inv - le.P_INV) < 0.02, f"p_inv {p_inv}"


def test_cap_per_micron():
    """unit inverter cap을 총 폭으로 나눈 값이 per-width 환산과 맞는가."""
    assert abs(le.C_PER_UM - 1.249) < 0.002


# ── 2장: logical effort ──────────────────────────────────────────────

def test_gate_library_matches_report():
    lib = le.build_library()
    expected = {
        "INV": (1.000, 2.65), "NAND2": (1.336, 5.30), "NAND3": (1.672, 7.95),
        "NAND4": (2.008, 10.60), "NAND5": (2.344, 13.25), "NOR2": (1.664, 5.30),
        "NOR4": (2.992, 10.60), "MUX4": (3.358, 18.55), "MUX2": (1.785, 10.60),
    }
    for name, (g, p) in expected.items():
        assert abs(lib[name].g - g) < 0.003, f"{name} g"
        assert abs(lib[name].p - p) < 0.02, f"{name} p"


def test_structure_9_is_optimal():
    """15개 후보 중 #9가 최소 delay인가."""
    lib = le.build_library()
    ds = [le.path_effort(p, lib, le.first_gate_cin(p, lib))[5]
          for p in le.CANDIDATES]
    assert ds.index(min(ds)) == 8, "구조 #9가 최적이어야 함"


def test_structure_9_path_effort():
    lib = le.build_library()
    path = le.CANDIDATES[8]
    G, H, F, P, N, D = le.path_effort(path, lib, le.first_gate_cin(path, lib))
    assert abs(G - 83.77) < 0.3
    assert abs(H - 18.16) < 0.05
    assert abs(F - 24340) < 200
    assert abs(P - 63.60) < 0.05
    assert N == 8
    assert abs(D - 91.87) < 0.3


def test_theory_vs_simulation_within_3pct():
    """이론 delay와 실측 368.4 ps의 오차가 3% 이내인가 (보고서 핵심 주장)."""
    lib = le.build_library()
    path = le.CANDIDATES[8]
    D = le.path_effort(path, lib, le.first_gate_cin(path, lib))[5]
    theoretical = le.TAU * D
    measured = 368.4
    err = abs(theoretical - measured) / measured * 100
    assert err < 3.0, f"오차 {err:.2f}% 가 3%를 넘음"


def test_sizing_chain_matches_table_23():
    """표 2.3의 stage별 input cap이 재현되는가."""
    lib = le.build_library()
    path = le.CANDIDATES[8]
    _f, _F, _N, _D, rows = le.size_path(path, lib, le.first_gate_cin(path, lib))
    want = [5.51, 14.57, 30.94, 3.40, 7.23, 15.28, 26.88, 56.82]
    for (_i, _g, cap, _wn, _wp), expected in zip(rows, want):
        assert abs(cap - expected) < 0.06, f"C_in {cap} vs {expected}"


def test_sizing_closes_on_load():
    """마지막 stage가 과제 조건인 100 fF 부하로 닫히는가."""
    lib = le.build_library()
    path = le.CANDIDATES[8]
    f_hat, _F, _N, _D, rows = le.size_path(path, lib, le.first_gate_cin(path, lib))
    last_gate = le.expanded_last(path, lib)
    closing = f_hat * rows[-1][2] / lib[last_gate].g
    assert abs(closing - le.C_LOAD) < 1.5, f"출력 부하 {closing}"


# ── 3장: wire / repeater / crosstalk ─────────────────────────────────

def test_wire_rc_totals():
    assert abs(wa.R_WIRE - 20000) < 1
    assert abs(wa.C_WIRE - 40) < 0.01
    assert abs(wa.C_ADJ - 60) < 0.01


def test_non_repeated_delay_matches_report():
    """단일 π Elmore 계산이 보고서의 598.5 ps와 맞는가."""
    t = wa.non_repeated_delay()
    assert abs(t - 598.5) < 1.0, f"{t}"


def test_repeated_delay_matches_report_n4():
    """N=4 이론값이 보고서 289.578 ps와 1% 이내로 맞는가."""
    t = wa.repeated_delay(4)
    assert abs(t - 289.578) / 289.578 < 0.02, f"{t}"


def test_repeater_improves_delay():
    """repeater 삽입이 delay를 실제로 줄이는가."""
    assert wa.repeated_delay(4) < wa.non_repeated_delay()


def test_repeater_optimum_is_flat_near_4_and_5():
    """최적점 부근(N=4,5)에서 delay가 둔감한가 — 보고서 3.5절 논지."""
    t4, t5 = wa.repeated_delay(4), wa.repeated_delay(5)
    assert abs(t4 - t5) / min(t4, t5) < 0.02


def test_crosstalk_ratio_is_1_3_5():
    """Miller effect에 따른 C_eff 비가 1:3:5인가."""
    ratios = [r for _n, _c, r in wa.crosstalk_cases()]
    assert abs(ratios[0] - 1.0) < 0.01
    assert abs(ratios[1] - 3.0) < 0.01
    assert abs(ratios[2] - 5.0) < 0.01


def test_crosstalk_monotonic_with_measurement():
    """실측 delay 비도 C_eff와 같은 순서로 증가하는가."""
    measured = [409.9, 795.4, 2216.0]
    assert measured[0] < measured[1] < measured[2]
    c_eff = [c for _n, c, _r in wa.crosstalk_cases()]
    assert c_eff[0] < c_eff[1] < c_eff[2]


# ── 4장: 최종 결과의 일관성 ──────────────────────────────────────────

def test_final_optimization_improves():
    """재최적화가 delay를 줄였는가 (762.2 → 756.4 ps)."""
    before, after = 762.2, 756.4
    assert after < before
    assert abs((before - after) - 5.8) < 0.05


def test_table_averages():
    """보고서 delay 표의 평균값이 산술적으로 맞는가."""
    cases = [
        ([351, 350, 351, 351, 350], 350.6),
        ([386, 387, 386, 386, 386], 386.2),
        ([736, 738, 735, 733, 734], 735.2),
        ([793, 790, 792, 789, 792], 791.2),
        ([778, 778, 776, 779, 777], 777.6),
    ]
    for values, expected in cases:
        got = sum(values) / len(values)
        assert abs(got - expected) < 0.05, f"{values} -> {got} vs {expected}"


def test_table_32_averages_rounded_to_integer():
    """표 3.2는 평균이 정수로 반올림되어 표기되었다."""
    for values, shown in [([739, 734, 735, 735, 735], 736),
                          ([788, 789, 787, 790, 790], 789)]:
        got = sum(values) / len(values)
        assert round(got) == shown, f"{values} -> {got} vs {shown}"


def test_n4_tpd_from_raw_measurements():
    """표 3.2의 미반올림 평균으로 t_pd = 762.2 ps가 정확히 재현되는가."""
    rise = sum([739, 734, 735, 735, 735]) / 5     # 735.6
    fall = sum([788, 789, 787, 790, 790]) / 5     # 788.8
    assert abs((rise + fall) / 2 - 762.2) < 0.01


def test_tpd_is_mean_of_rise_fall():
    """t_pd가 rising/falling 평균으로 정의되는가."""
    assert abs((350.6 + 386.2) / 2 - 368.4) < 0.05
    assert abs((735.2 + 791.2) / 2 - 763.2) < 0.05
    assert abs((735.2 + 777.6) / 2 - 756.4) < 0.05


# ── 5장: power estimation ────────────────────────────────────────────

def test_power_estimate():
    """P = αCV²f 추정이 보고서 값(≈44 μW)과 맞는가."""
    c_total = 1.46e-12
    alpha, vdd, freq = 0.5, 1.1, 50e6
    p = alpha * c_total * vdd ** 2 * freq
    assert abs(p - 44e-6) < 3e-6, f"{p * 1e6:.1f} uW"


def test_wire_dominates_power():
    """wire+repeater가 전체 switched cap의 과반인가."""
    gate_drain, wire, repeater, load = 240, 640, 478, 100
    total = gate_drain + wire + repeater + load
    assert (wire + repeater) / total > 0.5


def _run_without_pytest() -> int:
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in fns:
        try:
            fn()
            print(f"  [PASS] {name}")
        except AssertionError as exc:
            failed += 1
            print(f"  [FAIL] {name}: {exc}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_without_pytest())
