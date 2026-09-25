# 16-bit Bus 설계 — Combinational Circuit 기반 (디지털전자회로 Project)

연세대학교 디지털전자회로(정성욱 교수님) 프로젝트. 16-bit 비교 로직(1's detector)과 16:1 MUX로 구성된 bus system을 45 nm / V_DD 1.1 V 조건에서 설계하고, **logical effort로 예측한 delay와 SPICE 시뮬레이션을 정량 비교 검증**했다.

문서만 있는 저장소가 아니라, **설계 계산 코드와 SPICE 테스트벤치가 함께 들어 있어 결과를 그대로 재현·검증할 수 있다.**

## 결과 요약

| 단계 | t_pd (측정) | 이론값 | 오차 |
|---|---|---|---|
| Source→Destination (wire 미포함) | 368.4 ps | 378.6 ps | **2.77%** |
| + Non-repeated wire (200 μm) | 1030.5 ps | 977.1 ps | 5.2% |
| + Repeater 최적화 (N=4) | 762.2 ps | 668.2 ps | 14.1% |
| + 재설계·sizing 재최적화 | **756.4 ps** | — | 최종 |

- **기초 측정**: C_inv(unit)=4.1216 fF, C_d,n=0.5930 fF / C_d,p=1.405 fF, τ=4.121 ps, p_inv=2.650
- **구조 탐색**: 15개 logic 후보의 logical effort 비교 → NAND2-NOR2-NAND4-NOR2-MUX4-MUX4 (8-stage, D=91.87τ)
- **Metal line**: π-model + Elmore delay, R_eff 실측 기반 driver/repeater 모델링, N=3/4/5 스윕
- **Crosstalk**: Miller effect 3-case (C_gnd : +C_adj : +2C_adj = 1:3:5) → 실측 delay 비 1 : 1.94 : 5.41
- **설계 인사이트**: 이론상 최적이던 NAND5 기반 MUX가 실측에서 더 느림(직렬 스택 과다) → NAND3/NAND4 재최적화 + input reordering으로 회복

## 저장소 구성

```
├── 디지털전자회로_Project_보고서.md / .docx / .pdf   보고서 본문
├── 시뮬레이션_재현_가이드.md / .docx / .pdf          재현 가이드 (Linux/Windows)
├── tools/            설계 계산 코드 (Python, 의존성 없음)
│   ├── logical_effort.py    구조 탐색 · sizing · 보고서 값 검산
│   ├── wire_analysis.py     Elmore delay · repeater 최적화 · crosstalk
│   └── test_design.py       회귀 테스트 22종
└── sim/              SPICE 테스트벤치 (ngspice)
    ├── lib_gates.sp             sizing 반영 gate 라이브러리
    ├── tb0a_gatecap.cir         gate cap 추출 (slope matching)
    ├── tb0b_draincap.cir        drain cap 추출
    ├── tb0d_fo_delay.cir        FO1/FO4 → τ, p_inv
    ├── tb1_source_dest_path.cir 8-stage critical path
    ├── tb2_logic_check.cir      기능 검증 (XNOR → 1's detector → MUX)
    ├── tb3_wire_nonrepeated.cir π-model wire
    ├── tb4_wire_repeated_n4.cir repeater N=4
    ├── tb5_crosstalk.cir        crosstalk 3-case
    └── tb6_full_link.cir        source→wire→destination 전체 경로
```

## 실행

**설계 계산 검증** (Python 3.9+, 외부 의존성 없음)

```bash
python tools/logical_effort.py     # 표 2.1~2.4 생성 + 보고서 값 26건 검산
python tools/wire_analysis.py      # wire delay, 최적 N 스윕, crosstalk
python tools/test_design.py        # 회귀 테스트 22종
```

`logical_effort.py`는 후보 15종의 path effort를 직접 계산해 보고서 표 2.2를 재생성하고,
stage별 sizing이 과제 조건인 100 fF 부하로 정확히 닫히는지까지 확인한다.

**SPICE 시뮬레이션** (ngspice + [PTM 45 nm](https://ptm.asu.edu) 모델)

```bash
cd sim
# 45nm_HP.pm 을 이 폴더에 배치한 뒤
ngspice -b tb0d_fo_delay.cir
ngspice -b tb4_wire_repeated_n4.cir
```

학교 PDK가 아닌 공개 모델이므로 절대값은 다르고 **경향이 재현**된다. 기대 결과는 재현 가이드 §3 체크리스트 참조.

## 문서

| 파일 | 내용 |
|---|---|
| [디지털전자회로_Project_보고서.md](디지털전자회로_Project_보고서.md) | 보고서 본문 (1~7장 + 부록 A·B) |
| [시뮬레이션_재현_가이드.md](시뮬레이션_재현_가이드.md) | Linux(Cadence Virtuoso+Spectre) / Windows(원격 접속 또는 ngspice 대체) 재현 절차 |
| [sim/README.md](sim/README.md) | 테스트벤치별 실행법과 보고서 대응표 |
