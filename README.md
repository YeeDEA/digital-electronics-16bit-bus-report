# 디지털전자회로 Project — 16-bit Bus 설계 보고서 (복원 프로젝트)

연세대학교 디지털전자회로(정성욱 교수님) 수업에서 **직접 수행한 프로젝트 〈Combinational circuit을 이용한 16-bit bus 설계〉** 의 보고서입니다.

원본 보고서 파일(Google Docs)이 유실되어, 당시 화면을 촬영해 둔 사진 70장과 수업 전사 기록을 근거로 보고서 전체를 복원했습니다. 사진 70장을 전수 판독하고 핵심 수치 41건을 확대 재검증하여, 어디까지가 원본 판독이고 어디부터 재구성인지(`[복원]`, `(저신뢰)` 표기) 구분해 두었습니다.

## 문서

| 파일 | 내용 |
|---|---|
| [디지털전자회로_Project_보고서_복원본.md](디지털전자회로_Project_보고서_복원본.md) | 복원 보고서 본문 (마크다운 원본) |
| 디지털전자회로_Project_보고서_복원본.docx / .pdf | 제출용 포맷 (pandoc + LibreOffice 변환, 31쪽) |
| [시뮬레이션_재현_가이드.md](시뮬레이션_재현_가이드.md) | 전체 측정을 다시 돌리는 방법 — Linux(Cadence Virtuoso+Spectre) / Windows(원격 접속·ngspice+PTM 45nm) |
| 시뮬레이션_재현_가이드.docx / .pdf | 〃 변환본 |

## 설계 요약

- **과제**: 16-bit 비교기(1's detector) + 16:1 MUX를 갖는 bus system을 45 nm, V_DD 1.1 V에서 설계. Logical effort로 예측한 delay와 SPICE 시뮬레이션을 비교 검증.
- **기초 측정**: C_inv(unit)=4.1216 fF, C_d,n=0.5930 fF / C_d,p=1.405 fF, τ=4.121 ps, p_inv=2.650 (FO1/FO4 = 15.04/27.40 ps)
- **Source/Destination**: 15개 logic 후보 비교 → NAND2-NOR2-NAND4-NOR2-MUX4-MUX4 (8-stage, D=91.87τ) 선정 → 시뮬레이션 368.4 ps vs 이론 378.6 ps (**오차 2.77%**)
- **Metal line**: π-model + Elmore delay, R_eff 측정(452/470 Ω), non-repeated 1030.5 ps → repeater N=4에서 **762.2 ps** (약 250 ps 개선), crosstalk 3-case delay 비 1 : 1.94 : 5.41 (Miller effect)
- **재설계**: NAND5 MUX가 이론과 달리 느려진 원인 분석 → NAND3/NAND4 재최적화 + input reordering → 최종 **756.4 ps**

## 부록 구성

- **부록 A** — 사진 70장 ↔ 보고서 그림/표 전수 매핑
- **부록 B** — 정한울 교수님 커리큘럼(디지털집적회로) 기반이었다면 프로젝트가 어떻게 달라졌을지 비교 분석
- **부록 C** — Cadence Virtuoso 측정 절차 기록 (TSMC28 튜터링 세션)
- **부록 D** — 복원 검증 로그: 정정 이력, 원본 오탈자 8건, 결측 자료 11건 목록

> 복원 근거가 된 사진 원본(KakaoTalk_*.jpg/png)은 강의실 배경 등 개인정보가 포함되어 있어 저장소에는 포함하지 않았습니다 (로컬 보관).
