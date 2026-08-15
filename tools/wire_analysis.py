#!/usr/bin/env python3
"""
wire_analysis.py — bus metal line의 Elmore delay 분석과 repeater 개수 최적화

보고서 3장(Metal Line 설계)의 계산을 재현한다.
  · non-repeated wire delay (단일 π 등가 모델)
  · repeater N개 삽입 시 delay와 최적 N 탐색
  · crosstalk 3-case의 effective capacitance 비교

사용법:
    python wire_analysis.py             # 전체 분석 출력
    python wire_analysis.py --sweep 12  # N을 1..12까지 스윕
"""

from __future__ import annotations

import argparse

# ── 배선 조건 (과제 제공) ─────────────────────────────────────────────
L_UM = 200.0          # 배선 길이 [μm]
R_W = 100.0           # 단위길이 저항 [Ω/μm]
C_W = 0.2             # 단위길이 커패시턴스 [fF/μm]
C_ADJ_PER_UM = 0.3    # 인접 배선 결합 커패시턴스 [fF/μm]

R_WIRE = R_W * L_UM   # 20 kΩ
C_WIRE = C_W * L_UM   # 40 fF
C_ADJ = C_ADJ_PER_UM * L_UM   # 60 fF

# ── 측정으로 얻은 소자 상수 (보고서 1장·3.1절) ────────────────────────
R_DRIVER = 929.338    # NOR2 driver effective resistance [Ω]
R_INV = 929.338       # repeater inverter (driver와 동일 구동력) [Ω]
C_DRIVER = 10.839     # driver output cap [fF]
C_RECEIVER = 7.226    # receiver(NAND3) input cap [fF]
C_OUT_INV = 5.420     # repeater inverter output cap [fF]
C_IN_INV = 2.045      # repeater inverter input cap [fF]
T_FO1 = 15.04         # unit inverter FO1 delay [ps]

T_SOURCE = 378.6      # source 경로 이론 delay [ps] (보고서 2장)


def ohm_ff_to_ps(r_ohm: float, c_ff: float) -> float:
    """R[Ω] · C[fF] → delay [ps].  1 Ω · 1 fF = 1e-15 s = 1e-3 ps."""
    return r_ohm * c_ff * 1e-3


def non_repeated_delay() -> float:
    """단일 π 등가 모델의 Elmore delay [ps].

    t = (C_driver + C_w·l/2)·R_driver + (C_receiver + C_w·l/2)·(R_w·l + R_driver)
    """
    half_c = C_WIRE / 2
    term1 = ohm_ff_to_ps(R_DRIVER, C_DRIVER + half_c)
    term2 = ohm_ff_to_ps(R_WIRE + R_DRIVER, C_RECEIVER + half_c)
    return term1 + term2


def repeated_delay(n: int) -> float:
    """repeater로 wire를 n등분했을 때의 총 delay [ps].

    구간 하나당 Elmore delay를 구하고, 마지막 구간만 부하가 receiver다.
    구간 사이의 inverter delay (n-1개)를 더한다.
    """
    r_seg = R_WIRE / n
    half_c_seg = C_WIRE / (2 * n)

    # 중간 구간: 부하가 다음 repeater의 input cap
    t_mid = (ohm_ff_to_ps(R_INV, C_OUT_INV + half_c_seg)
             + ohm_ff_to_ps(r_seg + R_INV, C_IN_INV + half_c_seg))
    # 마지막 구간: 부하가 receiver
    t_last = (ohm_ff_to_ps(R_INV, C_OUT_INV + half_c_seg)
              + ohm_ff_to_ps(r_seg + R_INV, C_RECEIVER + half_c_seg))
    # 첫 구간은 driver가 구동
    t_first = (ohm_ff_to_ps(R_DRIVER, C_DRIVER + half_c_seg)
               + ohm_ff_to_ps(r_seg + R_DRIVER,
                              (C_IN_INV if n > 1 else C_RECEIVER) + half_c_seg))

    if n == 1:
        return t_first
    return t_first + (n - 2) * t_mid + t_last + (n - 1) * T_FO1


def crosstalk_cases() -> list[tuple[str, float, float]]:
    """Miller effect 3-case의 effective capacitance와 상대비."""
    c_gnd = C_WIRE * 0.75      # 관찰 세그먼트 기준 유효 접지 cap (보고서 기준 30 fF)
    cases = [
        ("case 1  B가 동일 방향 transition", c_gnd),
        ("case 2  B가 고정 (quiet)", c_gnd + C_ADJ),
        ("case 3  B가 반대 방향 transition", c_gnd + 2 * C_ADJ),
    ]
    base = cases[0][1]
    return [(name, c, c / base) for name, c in cases]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sweep", type=int, default=8,
                        help="repeater 개수 N을 1..SWEEP까지 스윕 (기본 8)")
    args = parser.parse_args()

    print("=" * 68)
    print("배선 조건")
    print("=" * 68)
    print(f"  l        = {L_UM:.0f} um")
    print(f"  R_w      = {R_W:.0f} ohm/um   ->  R_wire  = {R_WIRE / 1000:.0f} kohm")
    print(f"  C_w      = {C_W:.1f} fF/um    ->  C_wire  = {C_WIRE:.0f} fF")
    print(f"  C_adj    = {C_ADJ_PER_UM:.1f} fF/um    ->  C_adj   = {C_ADJ:.0f} fF")
    print(f"  R_driver = {R_DRIVER:.3f} ohm,  C_driver = {C_DRIVER:.3f} fF")

    t_nr = non_repeated_delay()
    print()
    print("=" * 68)
    print("Non-repeated wire (단일 pi 등가, Elmore)")
    print("=" * 68)
    print(f"  t_wire            = {t_nr:.2f} ps")
    print(f"  t_total (+source) = {T_SOURCE + t_nr:.1f} ps")
    print(f"  시뮬레이션 실측       = 1030.5 ps  (보고서 3.3절)")
    print(f"  오차               = {abs(T_SOURCE + t_nr - 1030.5) / 1030.5 * 100:.1f} %")

    print()
    print("=" * 68)
    print(f"Repeater 개수 최적화 (N = 1..{args.sweep})")
    print("=" * 68)
    print(f"  {'N':>3} {'구간 R':>10} {'wire delay':>13} {'total (+source)':>17}")
    best_n, best_t = 1, float("inf")
    for n in range(1, args.sweep + 1):
        t = repeated_delay(n)
        mark = ""
        if t < best_t:
            best_n, best_t = n, t
        print(f"  {n:>3} {R_WIRE / n / 1000:>8.2f}k {t:>12.1f} ps {T_SOURCE + t:>14.1f} ps{mark}")
    print(f"\n  → 최적 N = {best_n} (wire delay {best_t:.1f} ps, repeater {best_n - 1}개)")
    print(f"     보고서 실측 최적: N = 4, 762.2 ps (repeater 3개)")
    print(f"     non-repeated 대비 개선: {t_nr - repeated_delay(4):.1f} ps (이론)")

    print()
    print("=" * 68)
    print("Crosstalk — Miller effect에 따른 effective capacitance")
    print("=" * 68)
    print(f"  {'Case':<34}{'C_eff [fF]':>12}{'상대비':>10}")
    for name, c_eff, ratio in crosstalk_cases():
        print(f"  {name:<34}{c_eff:>12.1f}{ratio:>10.2f}")
    print(f"\n  시뮬레이션 실측 delay 비 = 1 : 1.940 : 5.406  (보고서 3.6절)")
    print(f"  → delay가 C_eff에 대체로 비례하나, Miller 근사 때문에 정비례하지는 않음")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
