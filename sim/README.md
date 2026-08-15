# sim/ — ngspice 재현 테스트벤치

보고서의 측정을 오픈소스 환경(ngspice + PTM 45 nm)에서 재현하는 netlist 모음이다.
학교 PDK가 아닌 공개 모델이므로 **절대값은 다르고 경향이 재현**된다. (기대 결과는 `../시뮬레이션_재현_가이드.md` §3 체크리스트 참조)

## 준비

1. ngspice 설치 — Windows: https://ngspice.sourceforge.io 릴리스 zip / Linux: `sudo apt install ngspice`
2. PTM 45 nm HP 모델 다운로드 — https://ptm.asu.edu 에서 45nm_HP 모델 카드를 받아 이 폴더에 `45nm_HP.pm`으로 저장
   (라이선스상 모델 파일은 저장소에 포함하지 않는다)

## 실행

```bash
ngspice -b tb0a_gatecap.cir     # gate cap 추출 (slope matching, C 스윕)
ngspice -b tb0b_draincap.cir    # drain cap 추출
ngspice -b tb0d_fo_delay.cir    # FO1/FO4 delay → τ, p_inv
ngspice -b tb3_wire_nonrepeated.cir   # π-model wire (l=200μm, 20kΩ/40fF)
ngspice -b tb4_wire_repeated_n4.cir   # repeater N=4
ngspice -b tb5_crosstalk.cir    # crosstalk 3-case (Miller effect)
```

## 파일 ↔ 보고서 대응

| 파일 | 보고서 절 | 확인 포인트 |
|---|---|---|
| tb0a_gatecap.cir | §1.1 | trA≈trB가 되는 CG = gate cap |
| tb0b_draincap.cir | §1.2 | drain cap (n/p 비대칭) |
| tb0d_fo_delay.cir | §1.4 | τ=(t_FO4−t_FO1)/3, p_inv=t_FO1/τ−1 |
| tb3_wire_nonrepeated.cir | §3.2~3.3 | wire 추가 시 delay 급증 |
| tb4_wire_repeated_n4.cir | §3.5 | repeater로 delay 감소 (N sweep은 파라미터 수정) |
| tb5_crosstalk.cir | §3.6 | case1:2:3 delay 비 ≈ C_eff 비 |
