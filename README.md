# 디지털전자회로 Project — Combinational Circuit을 이용한 16-bit Bus 설계

연세대학교 디지털전자회로(정성욱 교수님) 프로젝트. 16-bit 비교 로직(1's detector)과 16:1 MUX로 구성된 bus system을 45 nm / V_DD 1.1 V 조건에서 설계하고, **logical effort로 예측한 delay와 SPICE(Spectre) 시뮬레이션을 정량 비교 검증**했다.

## 결과 요약

| 단계 | t_pd (simulated) | 이론값 대비 |
|---|---|---|
| Source (wire 미포함) | 368.4 ps | 오차 **2.77%** (378.6 ps) |
| + Non-repeated wire (200 μm) | 1030.5 ps | 오차 12.5% |
| + Repeater 최적화 (N=4) | 762.2 ps | 약 250 ps 개선 |
| + 재설계·sizing 재최적화 | **756.4 ps** | 최종 |

- **기초 측정**: C_inv(unit)=4.1216 fF, C_d,n=0.5930 fF / C_d,p=1.405 fF, τ=4.121 ps, p_inv=2.650 (FO1/FO4 = 15.04/27.40 ps)
- **구조 탐색**: 15개 logic 후보의 logical effort 비교 → NAND2-NOR2-NAND4-NOR2-MUX4-MUX4 (8-stage, D=91.87τ) 선정
- **Metal line**: π-model + Elmore delay, R_eff 실측 기반 driver/repeater 모델링, repeater 개수 N=3/4/5 스윕
- **Crosstalk**: Miller effect 3-case (C_gnd : +C_adj : +2C_adj = 1:3:5) → delay 비 1 : 1.94 : 5.41 실측
- **재설계 인사이트**: 이론상 최적이던 NAND5 MUX가 실측에서 더 느림(직렬 스택 과다) → NAND3/NAND4 재최적화 + input reordering으로 회복

## 문서

| 파일 | 내용 |
|---|---|
| [디지털전자회로_Project_보고서.md](디지털전자회로_Project_보고서.md) | 보고서 본문 (마크다운 원본) |
| 디지털전자회로_Project_보고서.docx / .pdf | 제출용 포맷 |
| [시뮬레이션_재현_가이드.md](시뮬레이션_재현_가이드.md) | 전체 측정 재현 방법 — Linux(Cadence Virtuoso+Spectre) / Windows(원격 접속 또는 ngspice+PTM 45nm 대체 재현) |
| 시뮬레이션_재현_가이드.docx / .pdf | 〃 변환본 |

## 부록

- **부록 A** — 시뮬레이션 환경 및 측정 규약 (550 mV 교차 t_pd, 220/880 mV rise/fall, 5회 평균)
- **부록 B** — 타 커리큘럼(디지털집적회로) 관점 비교: wire-aware 설계 vs logic family 최적화
