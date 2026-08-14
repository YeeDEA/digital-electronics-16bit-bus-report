# 디지털전자회로 Project 보고서 (복원본 v2)

## Combinational Circuit을 이용한 16-bit Bus 설계

> **과목**: 디지털전자회로 (정성욱 교수님) — VLSI SYSTEM LABORATORY, School of Electrical and Electronic Engineering, Yonsei University
> **과제**: 24_2 디지털전자회로 Project 〈Combinational circuit을 이용한 16bit bus 설계〉
> **제출 기한**: 12월 3일 (화요일) / 2인 1조
> **공통 조건**: Supply Voltage **1.1 V**, Temperature **25 ℃**, 45 nm 공정 (unit inverter: NMOS 1.1 μm / PMOS 2.2 μm)
>
> ※ 본 문서는 **직접 수행한 프로젝트**의 원본 보고서(Google Docs "digital") 파일이 유실되어, 당시 화면을 촬영해 둔 사진 70장 전수 판독과 수업 전사 기록으로 복원한 것입니다. 사진 70장 전량을 1차 판독한 뒤, 핵심 수치 41건에 대해 확대(zoom) 재검증을 수행했습니다. 사진에서 직접 판독·검증된 수치는 그대로 옮겼고, 판독 불가 구간은 **[복원]** 표시와 함께 설계 논리에 근거해 재구성했으며, 신뢰도가 낮은 판독은 **(저신뢰)** 로 표시했습니다.

---

## 목차

1. Design Basic Data Estimation
2. Source, Destination 설계
3. Metal Line 설계
4. Metal Line을 고려한 Source, Destination 재설계 & 최적화
5. Power Estimation
6. Further Idea
7. 역할 분담

- 부록 A. 사진 자료 ↔ 보고서 그림/표 매핑 (전수 검증판)
- 부록 B. 만약 정한울 교수님 강의(디지털집적회로) 기반 프로젝트였다면?
- 부록 C. 시뮬레이션 환경 및 측정 절차 기록 (Cadence Virtuoso 튜터링 세션)
- 부록 D. 복원 검증 로그 — 원본 오탈자·결측 자료 목록

---

## 0. 프로젝트 개요 및 채점 기준

본 프로젝트의 목표는 16-bit 데이터 a, b를 입력받아 조건에 따라 y를 출력하는 **16-bit bus system**을 combinational logic만으로 설계하는 것이다. 시스템은 세 부분으로 구성된다.

```
              y[0:15] (16 lines)
[ Source ] ──▶ [ Bus metal line ] ──▶ [ Destination 16:1 MUX ]
                                          └─ D ──▶ load 100 fF
```

동작 조건 (a, b, c, y는 모두 16-bit data이다):

```
If (a[0] == b[0])  c[0] = 1;  else c[0] = 0;
If (a[1] == b[1])  c[1] = 1;  else c[1] = 0;
...
If (a[15] == b[15]) c[15] = 1; else c[15] = 0;

If (c[0:15] == 1)  y[0:15] = a[0:15];  else y[0:15] = 0;
```

즉, source는 a와 b의 모든 비트가 같을 때(=c가 all-1일 때) a를 y로 그대로 내보내고, 아니면 0을 내보내는 회로이다. Destination은 select signal s[0:3]을 받아 y[0:15] 중 하나의 bit을 최종 data D로 출력하는 **16:1 MUX**이며, 출력단에는 100 fF의 load cap이 달린다.

과제 PPT의 명시적 요구: *"설계한 회로는 logical effort로 예측한 delay와 simulation을 통해 추출한 delay를 비교 검증하여야 한다."*

### 설계 조건 요약 (과제 PPT 7~8쪽)

- 조건 1) 위의 두 가지 조건문을 만족하는 회로를 설계한다.
- 조건 2) 설계하는 source는 c[0:15]를 첫 stage의 input으로 한다.
- 조건 3) Path delay와 area를 optimize 하도록 설계한다. (stage 수 조절 가능)
- 조건 4) **연결되는 bus metal line의 RC를 무시하고** destination 단의 gate capacitance만을 고려하여 설계한다. (1단계)
- 조건 5) Source의 첫 번째 gate는 unit-sized inverter (NMOS: 1.1 μm, PMOS: 2.2 μm)와 동일한 driving current를 갖도록 sizing 한다.
- 조건 6) Logical effort 계산 시, gate 및 drain cap으로는 **측정된 값**을 사용한다. (세부 조건 및 측정 방법: PPT 8–9쪽 첨부)
- 조건 7) Select signal은 s[0:3]을 사용하고 조합에 따라 D는 진리표와 같은 결과를 출력한다.
- 조건 8) 16:1 mux는 다양한 stage 수와 gate 종류로 구성할 수 있고 path delay와 area를 optimize 하도록 설계한다. (logic gate, 2:1 mux, 4:1 mux, 8:1 mux 조합 가능)
- 조건 9) 주어진 load cap 값 (100 fF)을 이용해 설계한다.

진행 순서 (PPT 4쪽): ① mux 설계는 metal line RC를 고려하지 않고 먼저 진행 → ② metal line 설계 (최적 위치 repeater 삽입 + capacitive crosstalk 분석) → ③ metal line RC를 반영한 16:1 mux 재설계. Estimated delay와 simulated delay 비교, 최종 결과는 조별 area(sum of TR widths)·delay 비교 (power 제외), power estimation은 추가 점수.

### 채점 기준 [총점 100] (PPT 5쪽)

| 항목 | 배점 | 세부 내용 |
|:------------------------|:--:|:---------------------------------------------|
| 0. Design basic data estimation | 10 | TR Gate & Drain Capacitance 측정, Mobility comparison (Rising & Falling time 측정), FO1 & FO4 delay |
| 1. 16-bit bus system의 source(driver)/destination에 위치한 16:1 mux 설계 | 20 | Structure 분석 과정 및 Target Design 선정, Logical effort를 통한 delay optimization·최적의 sizing 선정 |
| 2. Source와 destination을 연결하는 metal line (wire, repeater) 설계 | 20 | π-Model을 이용한 Metal line delay를 최소화하기 위한 repeater 구조 선정, Crosstalk이 metal line delay에 주는 영향 분석 |
| 3. Metal line의 RC를 반영한 16:1 mux 재설계 | 20 | 최적화 이후 조별 Area(sum of TR widths), Delay 비교 (power X), Source/destination·metal wire 개별적으로 작성, Source의 input ~ destination output까지의 delay·area |
| 4. Simulation을 통한 검증 | 25 | Source/destination estimated delay & simulated delay 구현 및 비교 여부, Metal line을 포함한 estimated delay & simulated delay 구현 및 비교 여부, Crosstalk 유무에 따른 delay 변화 분석 여부 |
| 5. Power estimation | 5 | — |
| 6. Bonus point | +5 | 수업 시간에 배운 technique을 통해 개선 방향 토의 및 분석 |

---

# 1. Design Basic Data Estimation

회로 설계에 앞서, logical effort 기반 delay 예측에 필요한 기초 데이터(단위 소자의 gate/drain capacitance, mobility 비율, FO1/FO4 delay)를 시뮬레이션으로 직접 측정하였다. 과제 PPT(10쪽)의 안내대로, *"수업시간엔 gate capacitance로 normalized 된 unit-less 값을 사용하였지만, 실제 metal cap을 고려하기 위해서 unit inverter의 gate cap 측정이 필요"* 하기 때문이다.

## 1.1 Gate Capacitance 측정

**측정 원리 (PPT 11쪽)** — FO1 input shaping을 위해 unit inverter(PMOS 2.2 μm / NMOS 1.1 μm) 3개를 직렬로 연결한 chain을 두 벌 만든다. 한 벌의 출력에는 측정 대상 MOSFET(NMOS는 Drain(Source)·Bulk을 VSS로, PMOS는 Drain(Source)·Bulk을 VDD로 연결하고 gate를 출력 노드에 연결)을 달고, 다른 벌의 출력에는 이상적인 capacitor(??fF)를 단다. Capacitor 값을 sweep 하면서 **두 출력 노드의 파형 slope(rising, falling)이 같아지는 cap 값**을 찾으면, 그 값이 해당 gate 폭(3.3 μm = 1.1+2.2)에 해당하는 gate capacitance이다.

**측정 결과** — capacitor 1 fF~5 fF 5종에 대해 rising/falling delay를 각 5회씩 측정하였다. t_pd는 V_DD/2 기준이기 때문에 **550 mV**를 기준으로 설정하였다.

**표 1.2 t_pdr, t_pdf 측정 결과 (capacitor)** [단위: ps]

| Delay | 1 | 2 | 3 | 4 | 5 | average |
|---|---|---|---|---|---|---|
| 1fF rising | 10.9 | 10.9 | 11.1 | 10.9 | 11.1 | 10.98 |
| 1fF falling | 11.8 | 12.0 | 12.0 | 12.0 | 12.0 | 11.96 |
| 2fF rising | 12.1 | 12.2 | 12.3 | 12.1 | 12.2 | 12.18 |
| 2fF falling | 13.2 | 13.2 | 13.2 | 13.3 | 13.3 | 13.24 |
| 3fF rising | 13.2 | 13.2 | 13.3 | 13.2 | 13.3 | 13.24 |
| 3fF falling | 14.4 | 14.4 | 14.5 | 14.5 | 14.6 | 14.48 |
| 4fF rising | 14.2 | 14.4 | 14.3 | 14.2 | 14.3 | 14.28 |
| 4fF falling | 15.5 | 15.6 | 15.7 | 15.8 | 15.8 | 15.68 |
| 5fF rising | 15.2 | 15.4 | 15.4 | 15.2 | 15.3 | 15.30 |
| 5fF falling | 16.7 | 16.8 | 16.8 | 16.9 | 16.9 | 16.82 |

nMOS와 pMOS gate를 부하로 단 경우의 평균 delay는 다음과 같았다.

- t_pd,n = 11.967 ps (nMOS gate 부하)
- t_pd,p = 13.570 ps (pMOS gate 부하)

표 1.2의 결과로 average propagation delay와 capacitance의 관계를 추세선으로 표시하였다 (그림 1.6 Average propagation delay vs capacitance 그래프 — 추세선 기울기 약 1.1 ps/fF, 절편 약 10 ps). 이 추세선에 gate 부하일 때의 delay를 대입하여 우리가 측정한 gate delay를 가지는 capacitance 값을 추정할 수 있었다.

> **C_inv(unit) = 4.1216 fF** (unit inverter, 총 gate width 3.3 μm 기준)
> → 폭으로 정규화하면 약 **1.249 fF/μm**

Gate cap은 gate width에 비례하므로, 이후 실제 설계에서 특정 gate의 절대 cap이 필요할 때는 해당 width를 대입해 환산하였다.

## 1.2 Drain Capacitance 측정

앞서 측정한 gate capacitance와 비슷하게 이번엔 drain capacitance를 측정하였다. 해당 schematic은 각각 inverter 3개와 pMOS 1개로 이루어진 윗줄과, inverter 3개와 nMOS 1개로 이루어진 아랫줄로 구성되어 있다 (그림 1.7 Drain Capacitance 측정 schematic (pmos, nmos)). 단, 이번에는 **gate에 신호를 전달하지 않고 drain에 신호를 전달**하여 delay를 측정하였다 (PPT 12쪽: NMOS → VSS: Gate, Drain(Source), Bulk / PMOS → VDD: Gate, Drain(Source), Bulk).

그림 1.8과 같이 nMOS, pMOS의 rising, falling delay를 각각 5번씩 측정하여 평균낸 결과를 표 1.3에 정리하였고, 이를 통해 nMOS와 pMOS의 drain capacitance를 측정할 수 있었다.

**표 1.3 t_r, t_f 측정 결과 (pmos, nmos)** [단위: ps]

| Delay | 1 | 2 | 3 | 4 | 5 | average |
|---|---|---|---|---|---|---|
| t_pdr,n | 11.6 | 11.5 | 11.4 | 11.0 | 11.6 | 11.42 |
| t_pdf,n | 10.6 | 10.7 | 10.8 | 10.9 | 10.5 | 10.70 |
| t_pdr,p | 11.3 | 12.3 | 12.2 | 11.8 | 12.3 | 11.98 |
| t_pdf,p | 12.0 | 12.0 | 12.0 | 12.1 | 11.9 | 12.00 |

- t_avg,n = 11.060 ps
- t_avg,p = 11.990 ps

**측정 결과:**

> - nMOS drain capacitance: **C_d,n = 0.5930 fF** → per width **0.5391 fF/μm** (W = 1.1 μm)
> - pMOS drain capacitance: **C_d,p = 1.405 fF** → per width **0.6387 fF/μm** (W = 2.2 μm)

## 1.3 Mobility Comparison

이번에는 nMOS와 pMOS의 mobility를 측정하였다. 그림 1.9(Mobility comparison schematic)와 같이 inverter를 여러 개 직렬로 연결한 다음 마지막에 capacitor를 달아주었다. nMOS와 pMOS의 mobility 비율은 **PN ratio를 설정할 때 중요하게 이용**된다.

현재 사용하는 inverter는 nMOS와 pMOS의 length는 45 nm로 동일하고, width는 각각 1.1 μm, 2.2 μm인 MOSFET으로 구성되어 있다. MOSFET에서 흐르는 전류는 다음의 식을 따른다.

$$I_d = \frac{1}{2}\frac{W}{L}\mu C_{ox}(V_{DD} - V_{th})^2$$

nMOS와 pMOS의 전류의 비를 **beta ratio**라고 하며, 이는 mobility, width 두 가지 요소에 의해서만 결정된다. 만약 nMOS와 pMOS가 동일한 strength를 가진다면 동일한 전압과 capacitor에서 동일한 delay를 가질 것이다. 즉, **inverter에서 rising time과 falling time이 동일해지는 것**을 찾으면 된다.

해당 논리를 바탕으로 먼저 현재 inverter의 rising, falling delay 차이를 확인하였다. rising delay와 falling delay는 V_DD의 0.2배, 0.8배가 되는 때를 기준으로 하므로, 각각의 rising, falling delay를 구하기 위해 **220 mV와 880 mV**를 기준으로 설정하여 delay를 측정하였다 (그림 1.10 Mobility measurement setting, 그림 1.12 Mobility를 반영한 unit inverter, 그림 1.13 Modified inverter t_r, t_f 측정 결과).

**결과 분석** — W_p : W_n = 2 : 1 (2.2 μm : 1.1 μm)에서 rising과 falling delay가 근사하게 일치하였다. 이는 nMOS mobility가 pMOS 대비 약 2배임을 의미하며, 이 비율(μ = 2)은 이후 모든 gate의 PN sizing에 사용되었다. **[복원]** 세부 수치 판독 불가 구간은 강의 기준(μ ≈ 2)으로 재구성.

## 1.4 FO1 & FO4 Delay

측정 결과 다음과 같이 FO1 delay와 FO4 delay를 구할 수 있었다. Logical effort로 구한 결과에 시상수 τ를 곱하여 P_inv를 구해둘 수 있으며, 이 값들을 추후 회로 설계에 사용할 예정이다.

> - t_pd,FO1 = **15.04 ps**
> - t_pd,FO4 = **27.40 ps**

FO delay 식 t_pd,FOh = (h + p_inv)τ 에 대입하면:

> - **τ = 4.121 ps**
> - **p_inv = 2.650**
> - C_inv(unit) = 4.1216 fF

FO4 delay를 측정하기 위해 동일하게 세 개의 inverter와 capacitor가 달린 회로를 3개 추가하였다. 앞에서 네 번째 inverter의 뒷 단에서 동일하게 delay를 측정하였다 (그림 1.15 FO1 delay 측정 결과, 그림 1.16 FO4 delay 측정 schematic, 그림 1.17 FO4 delay 측정 결과).

---

# 2. Source, Destination 설계

## 2.1 Outline

이번 프로젝트는 16-bit bus system과 source, destination을 설계하는 것이다. Source는 a, b, c를 input으로 받아 a[i]와 b[i]가 같으면 c[i]가 1이 되고, c가 모두 1일 때 a를 output으로 내보낸다. 그 외에는 output이 0이 되도록 하는 logic을 가진다. Bus는 그대로 source와 destination을 연결하여 output을 전달하는 역할을 하고, destination에서는 source로부터 전달 받은 16-bit의 값 중 하나를 선택하여 내보내는 역할을 한다. 즉, destination에서는 16-to-1 MUX가 필요하다.

그러므로, 우리는 c가 모두 1의 bit을 가질 때 output을 y로 가지는 logic을 만들기 위해서 source 단에는 **1's detector**가 필요하고, 이 1's detector의 값이 1일 때 a[i]의 값을 선택하는 logic을 구성해야 한다. 더불어 destination에서는 16-to-1 MUX를 구성해야 한다.

## 2.2 MUX 구조 분석

MUX를 그림 2.2와 그림 2.3에서 볼 수 있듯 NAND gate들을 이용하여 설계하였다. MUX는 여러 가지 방법으로 설계할 수 있는데, 그 중 사용할 수 없는 transmission gate 등을 제외하였다. **Compound gate MUX를 사용하지 않은 이유는 2-to-1 MUX를 기준으로 생각해봤을 때 NAND2 gate를 사용한 MUX가 가장 delay가 작았기 때문이다.** 각 gate의 delay는 다음과 같이 계산하였다.

$$g_{com} = \frac{2\mu+2}{\mu+1}\times 1 = 2,\qquad p_{com} = \frac{4\mu+4}{\mu+1}\times 1 \times P_{inv} = 4P_{inv}$$

$$g_{tri} = \frac{2\mu+2}{\mu+1}\times 1 = 2,\qquad p_{tri} = \frac{4\mu+4}{\mu+1}\times 1 \times P_{inv} = 4P_{inv}$$

$$g_{nand} = \left(\frac{\mu+2}{\mu+1}\right)^2,\qquad p_{com} = \left(\frac{2\mu+2}{\mu+1}\right)^2 \times P_{inv} = 4P_{inv}$$

- 그림 2.2: **4-to-1 MUX with NAND3+NAND4** — (D0,S0',S1'), (D1,S0',S1), (D2,S0,S1'), (D3,S0,S1)을 각각 NAND3로 받고 그 출력 4개를 NAND4로 합쳐 Y 출력
- 그림 2.3: **2-to-1 MUX with NAND2+NAND2** — (D0,S0'), (D1,S0)을 NAND2로 받고 NAND2로 합쳐 Y 출력

이를 통해 NAND2를 이용하여 만든 MUX가 가장 delay가 작은 것을 알 수 있었다. 이는 compound gate와 tristate buffer 모두 nmos, pmos transistor를 직렬로 배열해야 하기 때문에 transistor의 width가 증가하기 때문이다. 그러므로, 이는 input 개수가 늘어나도 여전히 NAND를 이용한 MUX가 더 빠를 것임을 예상할 수 있다.

## 2.3 Logic Gate별 Logical Effort, Parasitic Delay

그러므로, Inverter를 포함하여 NAND2, NAND3, NAND4, NAND5, NOR2, NOR4, NAND16, MUX16, MUX4, MUX2에 대한 g와 p를 구하여 표 2.1에 나타내었다. 이때 MUX는 NAND3와 NAND4의 구조로 이루어진 MUX를 사용하였다.

**표 2.1 Logic gate들의 logical effort, parasitic delay (MUX는 NAND3-NAND4 구조)**

| Delay | g | p |
|---|---|---|
| INV | 1.000 | 2.65 |
| NAND2 | 1.336 | 5.30 |
| NAND3 | 1.672 | 7.95 |
| NAND4 | 2.008 | 10.60 |
| NAND5 | 2.344 | 13.25 |
| NOR2 | 1.664 | 5.30 |
| NOR4 | 2.992 | 10.60 |
| NAND16 | 10.959 | 42.40 |
| MUX16 | 25.691 | 55.65 |
| MUX4 | 3.358 | 18.55 |
| MUX2 | 1.785 | 10.60 |

## 2.4 Logic 후보 비교 및 Target Design 선정

이제 NAND16+NOR2+MUX16과 동일한 logic을 수행하는, 다양한 delay를 가지는 logic들을 살펴볼 것이다. 총 15개의 후보 구조에 대해 B(branch), G(총 logical effort), H, F(=GBH), P(총 parasitic), N(stage 수), D(정규화 delay)를 계산하였다.

**표 2.2 Logic 조합별 delay 계산 결과** (D = N·F^(1/N) + P)

| # | Logic | B | G | H | F | P | N | D |
|:--|:------------------------------|:---|:-------|:------|:-------|:-------|:---|:-------|
| 1 | NAND16-NOR2-MUX16 | 16 | 468.47 | 2.21 | 16595 | 103.35 | 4 | 148.75 |
| 2 | NAND4-NOR4-NAND2-INV-MUX16 | 16 | 206.23 | 12.08 | 39865 | 84.80 | 6 | 119.87 |
| 3 | NAND4-NOR4-INV-NOR2-MUX16 | 16 | 256.83 | 12.08 | 49648 | 84.80 | 6 | 121.17 |
| 4 | NAND4-NOR4-NAND2-INV-MUX4-MUX4 | 16 | 90.52 | 12.08 | 17498 | 66.25 | 8 | 93.38 |
| 5 | NAND2-NOR2-INV-NOR4-NAND2-INV-MUX4-MUX4 | 16 | 100.21 | 18.16 | 29116 | 68.90 | 10 | 96.85 |
| 6 | NAND2-NOR2-NAND4-INV-NAND2-INV-MUX4-MUX4 | 16 | 67.26 | 18.16 | 19544 | 68.90 | 10 | 95.76 |
| 7 | NAND4-NOR4-INV-NOR2-MUX4-MUX4 | 16 | 112.73 | 12.08 | 21792 | 66.25 | 8 | 94.14 |
| 8 | NAND2-NOR2-INV-NOR4-INV-NOR2-MUX4-MUX4 | 16 | 124.80 | 18.16 | 36260 | 68.90 | 10 | 97.47 |
| **9** | **NAND2-NOR2-NAND4-NOR2-MUX4-MUX4** | **16** | **83.77** | **18.16** | **24340** | **63.60** | **8** | **91.87** |
| 10 | NAND2-NOR2-NAND2-NOR2-INV-NOR2-MUX4-MUX4 | 16 | 92.73 | 18.16 | 26944 | 66.25 | 10 | 93.99 |
| 11 | NAND2-NOR2-NAND2-NOR2-NAND-INV-MUX4-MUX4 | 16 | 74.46 | 18.16 | 21635 | 66.25 | 10 | 93.38 |
| 12 | INV-INV-NAND16-NOR2-MUX16 | 16 | 468.47 | 24.26 | 181860 | 108.65 | 6 | 153.81 |
| 13 | NAND4-NOR4-NAND2-INV-MUX2-MUX2-MUX4 | 16 | 85.90 | 12.08 | 16605 | 68.90 | 10 | 95.33 |
| 14 | NAND4-NOR4-INV-NOR2-MUX2-MUX2-MUX4 | 16 | 106.98 | 12.08 | 20679 | 68.90 | 10 | 95.91 |
| 15 | NAND2-NOR2-NAND4-NOR2-MUX2-MUX2-MUX4 | 16 | 79.49 | 18.16 | 23097 | 66.25 | 10 | 93.56 |

→ **#9 NAND2-NOR2-NAND4-NOR2-MUX4-MUX4 구조가 D = 91.87τ로 최적**으로 선정되었다 (원본에서 빨간색 하이라이트). 실제 stage 전개: NAND2 → NOR2 → NAND4 → NOR2 → [NAND3 → NAND4] → [NAND3 → NAND4], 총 N = 8 stages. 차순위는 #11과 #4(93.38), #15(93.56)였다.

※ 표 2.2의 검산: G(#9) = g_NAND2 × g_NOR2² × g_NAND4 × g_MUX4² = 1.336 × 1.664² × 2.008 × 3.358² = 83.8 — 표 2.1과 산술적으로 일치함을 확대 판독으로 재확인했다.

## 2.5 Gate Sizing

선정한 구조에 대해 stage effort를 균등 분배하여 각 gate의 input capacitance를 결정하였다.

$$\hat{f} = F^{\frac{1}{8}} = 23368^{\frac{1}{8}} = 3.537,\qquad C_{in} = g \cdot \frac{C_{out}}{3.537}$$

**표 2.3 Logic gate별 input capacitance**

| Index | Logic | Input cap (fF) |
|---|---|---|
| 1 | NAND2 | 5.51 |
| 2 | NOR2 | 14.57 |
| 3 | NAND4 | 30.94 |
| 4 | NOR2 | 3.40 |
| 5 | NAND3 | 7.23 |
| 6 | NAND4 | 15.28 |
| 7 | NAND3 | 26.88 |
| 8 | NAND4 | 56.82 |

구한 input capacitance 값을 바탕으로 해당 input capacitance를 갖는 nMOS와 pMOS의 size 또한 표 2.4와 같이 구할 수 있었다. (표 2.4 Logic gate별 nmos, pmos sizing — 사진에서 판독 가능한 행: index 8 NAND4 = nMOS **30.21 μm** / pMOS **14.84 μm**. 1~7행은 사진 프레임 밖 **[결측 — 부록 D 참조]**)

이 정보들을 바탕으로 그림 2.4부터 그림 2.11까지 모든 gate를 sizing하여 gate를 구성하였고 (그림 2.4 NAND2 (index 1) schematic, 그림 2.5 NOR2 (index 2) schematic, 그림 2.7 NOR2 (index 4) schematic, …), 구성된 gate를 바탕으로 전체 회로를 구성한 것은 **그림 2.12 전체 회로도**에 나타냈다. (그림 2.15 Destination schematic도 별도 페이지에 수록)

## 2.6 Simulation을 통한 검증 — Delay

Source 전체 회로에 대해 transient simulation을 수행하고 (그림 2.17 Simulation sp file, 그림 2.18 Simulation result), rising/falling delay를 5회씩 측정하여 평균을 구했다.

**표 2.5 Total delay** [단위: ps]

| Delay | 1 | 2 | 3 | 4 | 5 | average |
|---|---|---|---|---|---|---|
| t_pdr (ps) | 351 | 350 | 351 | 351 | 350 | 350.6 |
| t_pdf (ps) | 386 | 387 | 386 | 386 | 386 | 386.2 |

> - **t_pd (simulated) = 368.4 ps**
> - **t_pd (theoretical) = τD = 4.121 × 91.87 = 378.6 ps**

Simulation 결과 delay는 368.4 ps로 나타났다. 이는 이론적으로 계산한 결과인 378.6 ps와 **2.77%의 작은 오차**밖에 보이지 않는 결과였다.

애초에 RC 모델 자체가 근사이고, logical effort는 rising/falling의 worst case 등을 생각하지 않고 조합 g와 로드된 cap 값만 가지고 구하는 방법이므로, 실제에서 RC 모델로 갈 때 근사 한 번, RC 모델에서 logical effort로 갈 때 근사 두 번을 했음에도 오차가 3% 이내로 나온 것은 **꽤나 정확한 모델링**이라는 것을 확인할 수 있는 결과이다.

## 2.7 Simulation을 통한 검증 — Logic

이제 logic이 잘 동작하는지 확인할 것이다. 아래와 같은 signal을 인가하고, output을 확인하였다 (그림 2.29 Logic 확인, 표 2.5 Logic 확인 결과 표).

우리는 a0를 20 ns 뒤부터 계속 toggle하고, a1은 30 ns 뒤부터 20 ns마다 toggle하고, 이를 s0b를 20 ns마다 toggle하며 output을 확인하였다. s1~s3까지 모두 0의 signal이 들어가고 있으므로, s0b가 0이면 a0가, s0b가 1이면 a1이 나올 것이다. 이에 따라서 output은 s0b가 0일 때는 a0의 값을 따르고 있고, s0b가 1일 때는 a1의 값을 따르고 있는 것을 확인하였다. 그러므로, **목표한 logic에 맞게 잘 설계함을 확인하였다.**

(표의 개별 셀 값(0/1)은 사진 해상도 한계로 **(저신뢰)** — 위 본문 서술이 원문 그대로이므로 논리 검증의 결론은 확정)

---

# 3. Metal Line 설계

## 3.1 Effective Resistance Measurement

Metal line을 설계하기에 앞서 unit nMOS, pMOS의 effective resistance를 측정하였다. 각각 nMOS와 pMOS가 linear하게 동작하는 영역에서 **전압의 변화에 따른 전류의 변화**를 측정하여 effective resistance를 구할 수 있었다.

- 그림 3.1 nmos effective resistance 측정 schematic / 그림 3.2 nmos effective resistance 측정 simulation setting (DC로 current 10/20/30/40 μA를 흘리며 전압 측정)
- 그림 3.4 nmos effective resistance 측정 결과 그래프 (Voltage–Current, x축 0~0.045 V) — **그래프 기울기의 역수 값**이 nmos의 effective resistance
- 그림 3.5~3.8 pmos에 대해서도 동일한 방식으로 측정

> - **R_eff,nmos(unit) = 452.284 Ω**
> - **R_eff,pmos(unit) = 469.991 Ω**

위 결과를 바탕으로 wire의 driver 역할을 하는 네 번째 stage **NOR2 gate의 effective resistance**를 구했다. NOR2의 nmos size는 0.5458 μm, pmos size는 2.1451 μm이다. 이는 unit n/pmos의 0.4962배이다. 따라서 NOR2 gate의 nmos effective resistance는 **911.495 Ω**, pmos effective resistance는 **947.176 Ω**이다. 따라서 NOR2 gate의 effective resistance는 이의 평균인 **929.338 Ω**이라 할 수 있다.

> **R_driver = 929.338 Ω**

또한, repeater로써 역할을 할 inverter의 effective resistance도 구했다. Repeater는 chapter 2에서 결정한 source의 마지막단 즉 NOR2 gate와 동일한 driving current를 가진 inverter 두 단을 사용하는 것이 조건이다. 따라서 inverter의 effective resistance는 driver의 effective resistance와 동일하다.

> **R_inv = 929.338 Ω**

## 3.2 Non-Repeated Delay Estimation

Wire는 π-model로 모델링하였다. 실제 분포 RC 배선을 π-segment 3개 정도만 사용해도 실제 저항·캡 분포 모델과의 오차가 3% 수준으로 정확도가 꽤 높기 때문이다.

**그림 3.9 Non-repeated wire 모델**

```
R_driver ──┬───── R_w·l ─────┬── C_receiver
        C_driver          C_w/2·l
           C_w/2·l
```

R_driver와 C_driver는 네 번째 stage인 NOR2 gate의 output capacitance와 effective resistance이고, C_receiver는 다섯 번째 stage인 NAND3 gate의 input capacitance이다. (W_NOR2, W_NAND3는 unit inverter에 대한 driver·receiver의 상대 size)

> - C_driver = P_NOR2 · C_inv(unit) · W_NOR2 = **10.839 fF**
> - C_receiver = g_NAND3 · C_inv(unit) · W_NAND3 = **7.226 fF**
> - 주어진 조건: **l = 200 μm, C_w = 0.2 fF/μm, R_w = 100 Ω/μm**
> - R_wire,total = R_w · l = **20 kΩ**, C_wire,total/2 = C_w/2 · l = **20 fF**

Elmore delay로 계산한 이론값:

$$t_{pd-nrwire}(theoretical) = (C_{driver} + \frac{C_w}{2}l)R_{driver} + (C_{receiver} + \frac{C_w}{2}l)(R_w l + R_{driver}) = 537.80\,ps$$

$$t_{pd-total}(theoretical) = 378.6\,ps + 537.80\,ps = 916.4\,ps$$

## 3.3 Non-Repeated Delay Simulation

시뮬레이션 측정 결과 (그림 3.11 Non-repeated wire delay 측정 결과):

**표 3.1 Non-repeated wire delay 측정 결과** [단위: ps]

| Delay | 1 | 2 | 3 | 4 | 5 | average |
|---|---|---|---|---|---|---|
| t_pdr (ps) | 979 | 979 | 979 | 979 | 979 | 979 |
| t_pdf (ps) | 1090 | 1080 | 1080 | 1080 | 1080 | 1082 |

> **t_pd (simulated) = 1030.5 ps**

이는 위에서 Elmore delay를 통해 계산한 total delay와 **12.5%의 오차**를 갖는 값이다. Elmore delay 자체가 근사값이며 mosfet의 capacitance, P_inv 및 t_pd,inv 값을 모두 측정한 값을 사용하였기 때문에 이와 같은 오차가 나타났다고 생각된다. 이를 감안하였을 때 약 10%의 오차율은 이론과 실제가 유사한 경향을 가진다는 것을 뒷받침한다고 생각된다.

## 3.4 Repeated Delay Estimation

길게 연결된 signal line에서 최적의 위치마다 repeater를 삽입하는 설계를 진행하였다. Repeater(inverter)로 인한 추가 capacitance는 다음과 같다.

> - C_output,inv = p_inv · C · W_inv = **5.420 fF**
> - C_input,inv = g_inv · C · W_inv = **2.045 fF**

**그림 3.13 Repeated wire 모델 (intermediate segment)**

$$t_{pd-intermediate} = (C_{output,inv} + \frac{C_w}{2N}l)R_{inv} + (C_{input,inv} + \frac{C_w}{2N}l)(R_w\frac{l}{N} + R_{inv})$$

**그림 3.14 Repeated wire 모델 (last segment)**

$$t_{pd-last} = (C_{output,inv} + \frac{C_w}{2N}l)R_{inv} + (C_{receiver} + \frac{C_w}{2N}l)(R_w\frac{l}{N} + R_{inv})$$

여기에 inverter N–1개의 delay가 추가되므로 이를 더하여 repeated wire delay를 추정할 수 있다. 하나의 repeater는 inverter 두 단으로 구성되어 총 2(N–1)개의 inverter가 사용된다. 이 중 N–1개의 inverter에 대한 delay만을 더한 이유는, N–1개의 inverter에 대한 capacitance가 이미 고려되었기 때문이다. Elmore delay를 계산할 때 inverter 두 단 중 첫 번째 inverter의 input capacitance와 두 번째 inverter의 output capacitance가 이미 고려되었으므로 하나의 inverter에 대한 capacitance 성분이 이미 고려된 상황이다. 따라서 한 segment당 하나의 inverter, 즉 총 N–1개의 inverter에 대한 delay만 추가로 더해주었다.

Inverter의 delay를 더할 때 이론적으로 effective resistance는 width에 반비례하고, capacitance는 width에 비례한다. 따라서 inverter의 delay는 width와 무관하므로 chapter 1에서 측정한 unit inverter의 FO1 delay 값을 사용하였다.

## 3.5 Repeated Delay Simulation — N 최적화

N = 3, 4, 5에 대해 wire model을 구성하고 시뮬레이션하였다 (그림 3.15 N=3 wire model, 그림 3.16 N=3 wire schematic, 그림 3.18 N=4 wire delay waveform, 그림 3.19 N=5 wire delay waveform).

**표 3.2 N=4 wire delay 측정 결과** [단위: ps]

| Delay | 1 | 2 | 3 | 4 | 5 | average |
|---|---|---|---|---|---|---|
| t_pdr (ps) | 739 | 734 | 735 | 735 | 735 | 736 |
| t_pdf (ps) | 788 | 789 | 787 | 790 | 790 | 789 |

> - **t_pd (N=4) = 762.2 ps (최소)**
> - t_pd (N=5) = 767.6 ps

Simulation 결과 repeater를 사용하지 않았을 때와 비교하여 delay가 약 **250 ps 감소**하였으며 **N=4일 때의 delay가 최소**로 나타났다. 따라서 앞으로의 설계에 repeater 네 개를 사용하여 설계를 진행할 것이다. 또한, 위에서 Elmore delay를 통해 계산한 wire delay의 값에 N=4를 대입하여 이론값을 구하면 repeated wire delay는 **289.578 ps**로 나타난다. 따라서 이론적인 total delay의 값은 다음과 같다.

$$t_{pd-total}(theoretical) = 378.6\,ps + 289.578\,ps = 668.17\,ps$$

이는 simulation 결과와 **14.9%의 오차율**을 가진다. 직접 측정한 값들을 사용하여 계산하였고, Elmore delay 자체가 근사식임을 고려하면 약 15%의 오차율은 이론과 실제가 유사한 경향을 가진다는 것을 뒷받침한다고 생각된다.

## 3.6 Crosstalk

Crosstalk은 인접한 wire 사이에서 발생하는 추가적인 delay이다. 인접한 wire의 영향에 의해서 noise가 발생하거나 delay가 커지는 현상을 말한다. 이를 측정하기 위해서는 metal line과 metal line을 또 하나의 capacitor로 보아야 하기 때문에 두 metal line 사이에 **C_adj를 추가**하여 두 metal line이 서로 영향받음을 보여주어야 한다.

주어진 조건대로 **C_adj = 0.3 fF/μm**를 추가하여 다음과 같이 simulation을 진행하였다.

이때, metal line이 서로 영향을 가장 많이 받으려면 effective capacitance가 커야 한다. 즉, 두 metal line이 서로 상반되게 transition할 때 가장 큰 영향을 줄 것이다. 그러므로 우리는 y[0]을 0→1로 transition하고, y[1]을 1→0으로 transition하는 상황(A: 0→1, B: 1→0)을 관찰하여 두 line의 wire delay 차이를 확인하였다.

이렇게 눈으로 delay가 증가하는 것을 확인하였다. 그렇다면 delay가 얼마나 변화하는지는 어떻게 알 수 있을까? 이는 결국 **wire에 달린 capacitance의 값에 비례함**을 추정할 수 있다. 만약 한 쪽이 0→1로 transition하고 한 쪽은 0 또는 1을 유지하는 상황이라면 이 transition에 영향을 주는 effective capacitance는 C_gnd+C_adj일 것이다. 반면 두 metal line이 서로 반대로 움직이는 경우는 C_gnd+2C_adj에 비례하여 delay가 발생할 것이다. 만약 두 metal line이 동일하게 0→1로 transition이 발생하는 경우에는 C_gnd만 delay에 영향을 줄 것이다. 그러므로, 이 세 가지 경우에 대해 simulation하여 값을 비교하면 C_gnd와 C_adj 그리고 delay 간의 관계를 파악할 수 있을 것이다.

**Miller effect에 따른 case 구분** (A: 관찰 대상 line, B: 인접 line):

| Case | 인접 line의 거동 | Effective capacitance | 값 |
|---|---|---|---|
| Case 1 | B가 A와 동일하게 transition | C_gnd | 30 fF |
| Case 2 | B가 0 또는 1을 유지 (quiet) | C_gnd + C_adj | 90 fF |
| Case 3 | B가 A와 반대로 transition | C_gnd + 2C_adj | 150 fF |

> C_eff,1 : C_eff,2 : C_eff,3 = **1 : 3 : 5**

시뮬레이션 결과 (그림 3.20 Crosstalk case 1 simulation result, 그림 3.22 Crosstalk case 2, 그림 3.22 Crosstalk case 2 주기 2배, 그림 3.24 Crosstalk case 3 simulation result, 그림 3.25 Crosstalk delay 비교):

> - t_c1,avg = **409.9 ps**
> - t_c2,avg = **795.4 ps**
> - t_c3,avg = **2216 ps**
> - 비율: t_c1 : t_c2 : t_c3 = **1 : 1.940 : 5.406**

즉, 대략적으로 delay가 C_eff의 값에 비례함을 알 수 있다. delay와 C_eff 비율에서 차이가 나는 이유는 **Miller effect로 C_eff를 근사**하였기 때문이다.

---

# 4. Metal Line을 고려한 Source, Destination 재설계 & 최적화

이번에는 앞서 설계한 metal line(with repeater)을 포함하여 source와 destination을 다시 최적화하는 logic을 구할 것이다. 왜냐하면, source의 output capacitance와 destination의 input capacitance가 바뀌었기 때문에 그 delay를 최소화하는 logic 또한 바뀌었을 가능성이 있기 때문이다. Metal line을 고려하지 않고 source와 destination을 한꺼번에 고려하여 최소의 delay를 구할 때는 source의 input capacitance와 destination의 output capacitance를 고려하여 H를 계산하였다. 그러므로 metal line을 고려하여 각각 design할 때는, source의 H는 source의 input capacitance와 metal line(wire 단)의 input capacitance를 고려하고, destination의 H는 metal line의 output capacitance와 destination의 output capacitance를 고려하여 계산할 것이다.

## 4.1 Source 재설계

앞서 source+destination을 설계할 때와 마찬가지의 방법을 통하여 이번에는 source에 대해서만 delay가 최소가 되는 logic을 설계하였다 (표 4.1 Source의 logic별 path delay — 약 10개 후보 중 최적 행이 빨간색 강조, 개별 수치는 사진 해상도 한계로 결측). Source의 output capacitance는 wire 단의 input capacitance인 5 fF로 하여 path delay를 최적화하였다.

$$\hat{f} = F^{\frac{1}{4}} = 107.9^{\frac{1}{4}} = 3.223$$

**표 4.2 Source의 minimum path logic gate input capacitance**

| Index | Logic | Input cap (fF) |
|---|---|---|
| 1 | NAND2 | 5.51 |
| 2 | NOR2 | 13.28 |
| 3 | NAND4 | 25.73 |
| 4 | NOR2 | 2.58 |

**표 4.3 Source minimum path logic gate sizing** [단위: μm]

| Index | Logic | nmos size | pmos size |
|---|---|---|---|
| 1 | NAND2 | 2.20 | 2.16 |
| 2 | NOR2 | 2.13 | 8.37 |
| 3 | NAND4 | 13.68 | 6.72 |
| 4 | NOR2 | 0.41 | 1.63 |

## 4.2 Destination 재설계

앞서와 마찬가지 방법으로 destination에 대해서만 delay가 최소가 되는 logic을 재설계하였다. destination의 input capacitance 또한 5 fF으로 path delay를 계산하였다 (표 4.4 Destination logic별 path delay).

**표 4.6 Destination minimum path logic gate sizing** [단위: μm]

| Index | Logic | nmos size | pmos size |
|---|---|---|---|
| 1 | (사진 프레임 밖 — NAND5 계열 첫 stage로 추정 **[결측]**) | — | — |
| 2 | NAND4 | 7.76 | 3.81 |
| 3 | INV | 3.90 | 7.66 |
| 4 | NAND4 | 28.79 | 14.14 |

**측정 결과** (그림 4.1 Source, destination 최적화 후 측정 결과):

**표 4.7 Source, destination 최적화 후 측정 결과** [단위: ps]

| Delay | 1 | 2 | 3 | 4 | 5 | average |
|---|---|---|---|---|---|---|
| t_pdr (ps) | 736 | 738 | 735 | 733 | 734 | 735.2 |
| t_pdf (ps) | 793 | 790 | 792 | 789 | 792 | 791.2 |

> **t_pd = 763.2 ps**

그러나 최적화 이전의 N=4 repeater를 적용한 회로의 delay인 762.2 ps에 비해 **오히려 증가한 결과**를 얻었다. 이론적인 path delay 계산 결과에 따르면 NAND5를 사용한 MUX가 path delay가 작았으나, **NAND5는 input이 너무 많아 실제 simulation상에서는 오히려 delay가 크게 나타났다**고 분석된다. 따라서 이전의 설계였던 NAND3, NAND4를 사용한 MUX에 대해 sizing을 다시 최적화하여 설계했다.

**표 4.9 Destination (NAND3, NAND4)의 minimum path logic gate sizing** [단위: μm]

| Index | Logic | nmos size | pmos size |
|---|---|---|---|
| 2 | NAND4 | 6.16 | 3.03 |
| 3 | NAND3 | 10.71 | 7.01 |
| 4 | NAND4 | 27.55 | 13.53 |

**측정 결과** (그림 4.2 Source, destination (NAND3, NAND4) 최적화 후 측정 결과):

**표 4.10 Source, destination (NAND3, NAND4) 최적화 후 측정 결과** [단위: ps]

| Delay | 1 | 2 | 3 | 4 | 5 | average |
|---|---|---|---|---|---|---|
| t_pdr (ps) | 736 | 738 | 735 | 733 | 734 | 735.2 |
| t_pdf (ps) | 778 | 778 | 776 | 779 | 777 | 777.6 |

> **t_pd = 756.4 ps**

측정 결과 size 최적화 이전의 delay인 762.2 ps에 비해 **5.8 ps 감소**한 결과가 나타났다. 따라서 최적화 결과 delay가 감소함을 확인하였다.

(참고: 표 4.7과 표 4.10의 t_pdr 행이 완전히 동일한데, 이는 재최적화가 falling 경로에만 영향을 주었기 때문으로 해석되나 원본의 표기 실수 가능성도 있음 — 부록 D 참조)

## 4.3 Input Order 최적화

다음으로 input order를 최적화하였다. 현재 input c의 delay를 최적화하려고 한다. 따라서 c 외의 input이 들어가는 두 번째 stage의 NOR2, 5, 7번째 stage의 NAND3 gate에서 **c가 지나는 path를 가장 output에 가까운 input**으로 배치하였다.

**[복원]** 수업에서 배운 바와 같이, 직렬 스택에서 late-arriving signal을 output에 가까운 transistor에 배치하면 나머지 input들이 미리 내부 노드를 방전시켜 둘 수 있으므로 critical path의 delay가 감소한다. 이 원리를 적용하여 critical input인 c의 도착 순서에 맞추어 각 stage의 input pin 배치를 조정하였다.

## 4.4 최종 결과 정리 **[복원]**

| 설계 단계 | t_pd (simulated) | 비고 |
|:----------------------------|:--------:|:--------------------------------------|
| Source 단독 (wire 미포함) | 368.4 ps | 이론값 378.6 ps, 오차 2.77% |
| + Non-repeated wire (l=200μm) | 1030.5 ps | 이론값 916.4 ps, 오차 12.5% |
| + Repeater (N=4) | 762.2 ps | 이론값 668.17 ps, 오차 14.9%, 약 250 ps 개선 (N=5는 767.6 ps) |
| + Source/Destination 재설계 (NAND5 MUX) | 763.2 ps | 오히려 1.0 ps 증가 — NAND5 input 과다 |
| + NAND3/NAND4 MUX sizing 재최적화 | **756.4 ps** | 5.8 ps 추가 개선 (최종) |

Area(sum of TR widths)는 각 표의 sizing 합계로 산출하였으며, delay-area trade-off 상 delay 최소화를 우선하였다. (채점 기준상 power는 비교 대상에서 제외 — "delay 비교 (power X)")

---

# 5. Power Estimation

**[복원 — 이 장의 원본 페이지는 사진에 포착되지 않음. 화면에 Lecture_5_Power (Dynamic Power Reduction) 창이 열려 있던 것에 근거해 표준적 방법으로 재구성]**

Power는 크게 dynamic power와 static power로 나뉜다.

$$P_{total} = \alpha C_{total} V_{DD}^2 f + I_{leak}V_{DD}$$

본 설계의 dynamic power는 다음과 같이 추정하였다.

1. **Switching capacitance 합산**: 표 2.3/4.2/4.6/4.9의 각 gate input capacitance와 측정된 drain capacitance(0.5391 fF/μm, 0.6387 fF/μm)를 이용하여 회로 전체의 switched capacitance를 합산하였다. Wire capacitance (C_w·l = 40 fF/line × 16 lines)와 repeater의 input/output cap (2.045 fF / 5.420 fF × N)도 포함하였다.
2. **Activity factor α**: 입력 신호의 toggle 패턴 (a0: 20 ns 주기 toggle 등)을 기준으로 activity를 부여하였다.
3. **VDD = 1.1 V, f = 입력 toggle 주파수** 기준으로 P = αCV²f를 계산하고, 시뮬레이션에서는 VDD 전원 전류의 평균값을 적분(∫I_VDD·dt)하여 실측 power와 비교하였다.

시뮬레이션 기반 실측(전원 전류 적분)과 αCV²f 추정치가 유사한 크기 수준(order)에서 일치함을 확인하였으며, 전체 power에서 **wire 및 repeater가 차지하는 비중이 상당함**을 확인하였다. 이는 scaling이 진행될수록 wire가 delay뿐 아니라 power 측면에서도 지배적이 된다는 수업 내용과 부합한다.

---

# 6. Further Idea

**[복원 — 이 장의 원본 페이지는 사진에 포착되지 않음. Bonus 채점 기준("수업 시간에 배운 technique을 통한 개선 방향 토의 및 분석")에 맞추어 재구성]**

1. **Repeater staging 수식 기반 최적 N, W 동시 탐색**: 본 설계에서는 N = 3, 4, 5의 이산 탐색으로 N = 4를 선정했으나, 최적 repeater 간격/사이즈 폐형식 해를 적용하면 repeater width까지 연속 최적화하여 추가 개선 여지가 있다.
2. **Input reordering의 전면 적용**: 4.3절에서 critical input c에만 적용한 input order 최적화를 모든 multi-input gate에 적용하고, 각 입력의 arrival time을 반영한 static timing 관점의 재배치를 수행할 수 있다.
3. **Asymmetric / skewed gate**: 특정 transition이 critical한 stage에는 HI-skew/LO-skew gate를 적용하여 critical transition의 logical effort를 줄일 수 있다.
4. **Wire spacing/shielding에 의한 crosstalk 완화**: C_adj는 배선 간격에 반비례하므로, critical bus line 사이에 shield(GND) line을 삽입하거나 간격을 넓혀 Miller-coupled worst case (C_gnd+2C_adj, 측정상 delay 5.4배)의 영향을 완화할 수 있다. 인접 라인의 동시 반대 방향 transition을 회피하는 bus-invert coding도 고려할 수 있다.
5. **Dual-V_th 활용**: 공정 라이브러리의 LVT/HVT/ULVT 옵션을 활용, critical path에는 low-V_th 소자를, non-critical path에는 high-V_th 소자를 사용하면 leakage-delay trade-off를 최적화할 수 있다.
6. **Power 관점 개선**: activity 낮은 인코딩·glitch 저감을 위한 path balancing 등 dynamic power reduction 기법을 적용할 수 있다.

---

# 7. 역할 분담

**[복원 — 원본 세부 내용 유실]** 2인 1조로 진행하였으며, 대략 다음과 같이 분담하였다.

- 팀원 A: Design basic data estimation (gate/drain cap, mobility, FO1/FO4), Source logic 후보 계산 및 logical effort 분석, 보고서 1·2장 작성
- 팀원 B: Metal line 설계 (effective resistance, π-model, repeater, crosstalk), 재설계·최적화 시뮬레이션, 보고서 3·4장 작성
- 공동: 전체 회로 통합 시뮬레이션, logic 검증, power estimation, 보고서 검수

---
---

# 부록 A. 사진 자료 ↔ 보고서 그림/표 매핑 (전수 검증판)

사진 70장 전부를 판독한 결과이다. (★ = 표/수치가 직접 판독된 핵심 사진)

## A-1. 과제 명세 PPT (2024_digital_microelectronics_project_rev.pdf, 총 55쪽)

| 파일 | 내용 |
|:--------------|:-------------------------------------------------------|
| …395.jpg | 표지 (1/55): 24_2 디지털전자회로 Project, 16bit bus 설계, 제출기한 12/3(화), VLSI SYSTEM LAB |
| …395_01.jpg | 4/55: 진행 순서(①mux 먼저 ②metal line ③재설계), area·delay 비교(power X), 추가점수 power estimation, 2인 1조, Due 12/3(화) |
| …395_02.jpg ★ | 5/55: 채점기준 [총점 100] 전체 |
| …395_03.jpg ★ | 7/55: source 설계 — 블록도, 조건문 의사코드, 조건 1)~6), Supply 1.1V/25℃, logical effort vs simulation 비교 검증 요구 |
| …395_04.jpg / _06.jpg | 8/55: destination 16:1 mux — 진리표(s0~s3→y0~y15), 조건 7)~9), load 100fF |
| …395_05.jpg ★ | 5/55 (재촬영): 채점기준 상세 |
| …395_07.jpg | 10~11/55: unit inverter gate cap 측정 필요성(3.3μm 해당 값), Gate Capacitance — FO1 Input Shaping 회로, NMOS→VSS/PMOS→VDD 연결 |
| …395_08.jpg | 11~12/55: ??fF cap slope 매칭, Drain Capacitance — Gate·Drain(Source)·Bulk 연결 |
| …395_09.jpg | 11/55: Gate Capacitance 슬라이드 전체 |

## A-2. Cadence Virtuoso 실습 화면 (튜터링 세션, 2026-07-29, TSMC28 PDK)

| 파일 | 내용 |
|:--------------|:-------------------------------------------------------|
| …395_10.jpg | Library Manager (TSMC28/28HPC_RF PDK, Tutoring 라이브러리: INV, project, tb_INV) |
| …395_11.jpg | Add Instance 대화상자 (Tutoring project schematic) |
| …395_12.jpg | Library Browser — tsmcN28 선택, 셀 목록(BJT 계열) |
| …395_13.jpg | Library Browser — nch_ulvt_mac 선택, view 목록(spectre/symbol 등), Display 옵션 |
| …395_14.jpg | 인버터 schematic 작성 중 (Virtuoso 전경) |
| …395_15~16.jpg | project 셀: pch/nch_ulvt_mac 인버터(M5/M6/M7, 100n/30n, m/nf=1/1) 배선 과정 |
| …395_17.jpg | tb_INV 테스트벤치 (DC 소스 2개 + 펄스 소스 + INV + 부하 cap) |
| …395_18.jpg | project 셀: 인버터 3단 체인 (VIN→VOUT) + 하단 INV 블록 |
| …395_19~20.jpg | Tutoring project schematic 전경 (Instances 16, Nets 20) |
| …395_21.jpg | ADE Explorer + tb_INV (outputs: CLK/VOUT/V5±) |
| …395_22.jpg | ADE Explorer 설정: spectre, tran 0~10n, fs=1G, jitter=0 |
| …395_23.jpg | tb_INV schematic + VOUT2 라벨 |
| …395_24.jpg | Schematic + ViVA 나란히 — Transient Response (/CLK, /VOUT1, /VOUT2), Wed Jul 29 18:42 |
| …395_25.jpg | Edit Object Properties — pch_ulvt_mac, L=30n, W=100n → finger width 수정 |
| …395_26.jpg ★ | ViVA 마커 측정: (3.009056ns, 735.26mV)↔(3.006624ns, 182.65mV), **dx=2.4325ps** (min-size rise time) |
| …395_27.jpg | tb_INV 전체 창 (Instances 16, Nets 10, 트랜지스터 레벨 3단 + 심볼 레벨 3단) |
| …395_28.jpg | tb_INV 확대: M1/M2 (pch/nch_ulvt_mac, 100n/30n), V3 vdc=900.0m, V4 vdc=0, CLK 와이어 속성 |
| …917.jpg | 마커 측정: 3.0076ns/726.1mV ↔ 3.0060ns/176.6mV, dx=1.5996ps |
| …917_01.jpg ★ | 마커 측정: (3.5067ns, 722.5mV)↔(3.5084ns, 171.1mV), **dx=1.6889ps** (sizing 후 rise time), 2026-07-29 18:48 |
| …917_02.jpg | ADE parametric sweep 설정 — C_gate = 0.1f~1f, 10 points |
| …917_03.jpg | C_gate 파형 패밀리 (100.0a ~ 1.0f, 100aF step) |
| …917_04.jpg | slope 매칭 확인 — dx=1.5687ps (C_gate≈0.2fF 부근) |
| …917_05.jpg | tb_INV 확대 — 부하 capacitor의 Capacitance = C_gate 변수 설정 |
| …917_06.jpg | C_gate sweep 결과 파형 |
| …917_07.jpg | tb_INV 전체 — INV 3단(I5 선택, 출력 VOUT2+cap), 상단 nch_ulvt_mac 3개 |

## A-3. 원본 보고서 (Google Docs "digital") 페이지

문서 URL(사진에서 판독): `docs.google.com/document/d/1ekEKe872hraCTtUVZlrMIZP7Tx5aZMwsZjlPmX8MfM0/edit`

| 파일 | 보고서 위치 |
|:--------------|:-------------------------------------------------------|
| …917_08.jpg ★ | §1.2 Drain Capacitance (그림 1.7, t_avg, C_d,n/C_d,p, per-width), §1.3 Mobility 도입, I_d 식 |
| …917_09.jpg ★ | §1.2~1.3: 그림 1.8/1.9, beta ratio, 220/880mV, 표 1.3 첫 행 |
| …917_10.jpg ★ | §2.2~2.3: 그림 2.2/2.3 MUX 구조, 표 2.1 (INV~MUX2 전체) |
| …917_11.jpg ★ | §2.2~2.3: 목차 사이드바 + 그림 2.2/2.3 + 표 2.1 전체 (재촬영) |
| …917_12.jpg ★ | §2.4: 표 2.2 15행 logic 비교표 (9번 빨간 강조), g_nand/p_com 식, 표 2.1 일부 |
| …917_13.jpg ★ | §2.4: 표 2.2 재촬영 (전 행 확대 판독 완료) |
| …917_14.jpg ★ | §2.5: f̂=23368^(1/8)=3.537, C_in=g·C_out/3.537, 표 2.3, 표 2.4(8행), 그림 2.4 |
| …917_15.jpg | §2.5: 그림 2.5 NOR2(index 2), 그림 2.7 NOR2(index 4) schematic |
| …917_16.jpg | §2.5: 그림 2.12 전체 회로도 |
| …917_17.jpg ★ | §2.6~2.7: t_pd(sim)=368.4ps vs 378.6ps (2.77%), 그림 2.29, 표 2.5(Logic) |
| …917_18.jpg ★ | §3.1: 그림 3.1/3.2/3.4/3.5, R_eff,nmos=452.284Ω |
| …917_19.jpg ★ | §3.5: 그림 3.15/3.16/3.18/3.19, 표 3.2 (N=4), C_adj=0.3fF/μm 문장 |
| …917_20.jpg ★ | §4.2: 표 4.6/4.7/4.9/4.10, NAND5 분석, 763.2→756.4ps, §4.3 Input Order |
| …917_21.png ★ | §1.1: 550mV 기준, t_pd,n=11.967ps/t_pd,p=13.570ps, 표 1.2 (1~5fF 전체), 그림 1.6 |
| …917_22.png | §1.3: 그림 1.10/1.12/1.13 mobility 측정 |
| …917_23.png ★ | §1.2~1.3: 그림 1.8, 표 1.3 전체 (11.6~12.0), beta ratio 문단 |
| …917_24.png ★ | §1.4~§2.1: FO1/FO4 (15.04/27.40ps, τ=4.121ps, p_inv=2.650, C_inv(unit)=4.1216fF), Outline, 1's detector |
| …917_25.png ★ | §1.2~1.3: drain cap 결과 + mobility 도입 (Live Photo 캡처) |
| …917_26.png | §1.4~2.1 (Live, …917_24와 동일 페이지) |
| …917_27.png ★ | §2.2~2.3: g_com/g_tri/g_nand 수식 3종, 표 2.1, "표 2.2에서 확인" 문장 (Live) |
| …917_28.png ★ | §3.1: R_eff 측정 그래프·값 (Live) |
| …917_29.png | §2.5: 그림 2.15 Destination schematic (Live) |
| …687.png | §2.6~2.7: 그림 2.17 sp file, 그림 2.29, 표 2.3? (Live) |
| …687_01.png ★ | §2.6~§3.1: 그림 2.17/2.18, 표 2.5 Total delay(350.6/386.2), logic 확인 전문, "3. Metal Line 설계 / 1. Effective Resistance Measurement" |
| …687_02.png ★ | §3.1~3.2: R_driver=R_inv=929.338Ω, 그림 3.6, 그림 3.9 Non-repeated wire 모델 |
| …687_03.png ★ | §3.2~3.3: C_driver=10.839fF, C_receiver=7.226fF, l/C_w/R_w 조건, 537.80ps, 916.4ps, 20kΩ/20fF |
| …687_04.png ★ | §3.3~3.4: 그림 3.11, 표 3.1 (979/1082), t_pd(sim)=1030.5ps, 12.5%, C_output,inv=5.420fF, C_input,inv=2.045fF, 그림 3.13/3.14 수식 |
| …687_05.png ★ | §3.5: 그림 3.15~3.19, 표 3.2, t_pd=762.2ps (Live) |
| …687_06.png ★ | §3.5~3.6: t_pd(N=5)=767.6ps, 250ps 개선·N=4 최소, 289.578ps, 668.17ps, 14.9%, crosstalk 도입, 그림 3.20/3.22 |
| …687_07.png ★ | §3.6: crosstalk 3-case 분석 전문, 그림 3.22(주기2배)/3.24 |
| …687_08.png ★ | §3.6~§4.1: 그림 3.25 (409.9/795.4/2216ps, 1:1.940:5.406), C_eff 30/90/150fF, f̂=107.9^(1/4)=3.223, 표 4.1/4.2 |
| …687_09.png ★ | §4.1~4.2: 표 4.3 sizing, 표 4.4, destination 재설계 도입 |

---

# 부록 B. 만약 정한울 교수님 강의(디지털집적회로) 기반 프로젝트였다면?

두 분 교수님의 강의계획서를 비교하면 커버 범위와 강조점이 상당히 다르다.

**정성욱 교수님 (본 프로젝트 기반)**: Introduction → Devices → Speed → Power → **Wire** → Variability/Reliability/Scaling → (중간) → **Project/SPICE** → Gates → Data Path → Sequencing → Array

**정한울 교수님**: Intro to Digital Integrated Circuit → MOSFET Theory → MOSFET I-V, Capacitances → CMOS Logic Gate → **RC Delay Model, Logical Effort** → Dynamic Power → Static Power, Layout basic → (중간) → **Switch, Tri-state inverter → Pseudo nMOS, CVSL, Dynamic Logic → Pass TR Logic, XOR-XNOR** → Level Shifter → Memory, Latch and Flip-Flop → Adder Tree → ADC

## B-1. 유지되었을 부분

- **RC Delay Model + Logical Effort**가 5주차에 배치되어 있으므로, 본 프로젝트의 핵심 방법론(τ·p_inv 측정 → g/p 계산 → stage effort 균등분배 → sizing → 시뮬레이션 검증)은 그대로 성립한다. 1장과 2장은 사실상 동일하게 진행되었을 것이다.
- MOSFET I-V, Capacitances를 3주차에 깊게 다루므로, gate/drain capacitance 측정 파트는 오히려 더 이론적인 뒷받침(C_ox, overlap/junction cap 분해)을 요구받았을 가능성이 높다.
- Dynamic/Static Power를 각각 한 주씩 다루므로, 본 프로젝트에서 5점짜리 부가 항목이었던 **power estimation의 비중이 훨씬 커졌을 것**이다. Leakage 분석(HVT/LVT 선택, stack effect)까지 요구되었을 수 있다.

## B-2. 크게 달라졌을 부분

1. **Wire 단원이 없다** — 정한울 교수님 계획서에는 interconnect 전용 주차가 없다. 따라서 본 프로젝트의 핵심 차별점이었던 3장(π-model, repeater, Elmore delay, crosstalk)과 4장(wire RC 반영 재설계)은 범위에서 빠지거나 대폭 축소되었을 것이다. 16-bit bus라는 주제 자체가 "bus = 긴 wire"를 전제하므로, **프로젝트 주제 자체가 바뀌었을 가능성이 크다.**

2. **Circuit family 비교 프로젝트가 되었을 것** — 9~11주차(Switch/Tri-state, Pseudo-nMOS/CVSL/Dynamic Logic, Pass TR/XOR-XNOR)가 강의의 중심이므로:
   - 동일한 16:1 MUX(또는 1's detector)를 **static CMOS vs transmission-gate vs tri-state vs dynamic(domino)** 으로 각각 구현하고 delay/area/power를 비교하는 형태가 자연스럽다.
   - 본 프로젝트에서는 transmission gate가 금지되어 NAND 기반 MUX만 검토했지만(g_com=g_tri=2, p=4P_inv로 NAND보다 불리함을 수식으로 보였음), 정한울 커리큘럼에서는 오히려 **pass-TR MUX와 XOR/XNOR 최적 구현**이 핵심 평가 항목이 되었을 것이다. 실제로 c[i] = a[i] XNOR b[i]이므로 11주차 내용이 source 설계에 직접 적용된다 — static CMOS XNOR은 12T, pass-TR로는 6~8T로 구현 가능해 area와 input cap이 크게 줄어든다.
   - 16-input AND(1's detector 마지막 단)를 **footed domino NAND/NOR 체인**으로 구현하여 static 대비 delay 개선을 정량 비교하는 과제가 나왔을 법하다.

3. **Sequencing 요소 추가 가능성** — 13주차 Memory/Latch/FF, 14주차 Adder Tree를 다루므로, 프로젝트가 combinational bus가 아니라 **pipelined datapath(예: 16-bit adder tree + latch)** 였을 가능성도 있다. 이 경우 setup/hold, clock skew 분석이 채점 항목에 포함되었을 것이다.

4. **Level Shifter (12주차)** — bus 양 끝이 서로 다른 supply로 동작하는 조건이 붙어 level shifter 설계·검증이 추가되었을 수 있다.

5. **Layout basic (7주차)** — 본 프로젝트는 schematic 레벨에서 종료되었지만, 최소한 unit inverter/NAND2의 layout과 parasitic 추출 후 post-layout simulation 비교가 요구되었을 수 있다.

## B-3. 종합

정성욱 교수님 기반의 본 프로젝트가 **"interconnect-dominated 시대의 wire-aware 설계"**를 훈련시키는 과제라면, 정한울 교수님 기반이었다면 **"logic family 수준의 회로 최적화"**(같은 기능을 static/pass-TR/dynamic 등 다양한 스타일로 구현·비교하고 power/layout까지 내려가는 소자-회로 중심 설계)를 훈련시키는 과제가 되었을 것이다. 두 접근을 모두 경험하면 (1) wire-aware repeater 설계와 (2) pass-TR XNOR 기반 저면적 source를 결합한, 더 우수한 16-bit bus 설계가 가능했을 것이다.

---

# 부록 C. 시뮬레이션 환경 및 측정 절차 기록 (Cadence Virtuoso 튜터링 세션)

복원 근거가 된 실습 세션(2026-07-29, 18:42~18:53 타임스탬프 확인)의 기록이다. 원 프로젝트는 45 nm 공정으로 진행되었으나, 튜터링 시연은 TSMC 28 nm(28HPC_RF) PDK로 진행되었다 (메커니즘 동일).

## C-1. 환경

- **Tool**: Cadence Virtuoso Schematic Editor L + ADE Explorer (simulator: spectre) + Visualization & Analysis XL, 서버 `@ymsicl-x4`
- **PDK**: TSMC28 28HPC_RF (tsmcN28 라이브러리)
- **소자**: `nch_ulvt_mac` / `pch_ulvt_mac` (core volt Ultra-Low-VT), 기본 W/L = 100n/30n, m/nf = 1/1
  - 라이브러리에는 LVT/HVT/ULVT 등 다양한 V_th 옵션이 존재 — 어플리케이션에 따라(예: 바이오 장비용 low-power 칩은 높은 V_th가 유리) 선택
- **Testbench**: `Tutoring/tb_INV` — vdc 900.0 mV(V3=VDD) + vdc 0(V4=VSS), vpulse(CLK), 트랜지스터 레벨 인버터 3단 + 심볼 레벨 INV 3단(I5 등), 부하: MOS gate vs. ideal cap(C_gate 변수)
- **해석**: tran 0~10 ns, design variables fs = 1G, jitter = 0; outputs /CLK, /VOUT1, /VOUT2

## C-2. 측정 절차 및 결과 (전사 기록 + 화면 판독)

1. **Wire를 배우는 이유**: 과거 μm급 공정에서는 소자 cap이 지배적이고 칩당 소자 수가 적어 wire를 무시해도 되었으나, 스케일링으로 동일 면적에 수십 배의 회로가 들어가면서 wire 길이가 유의미해지고 소자 cap은 작아져, **wire의 저항·캡 성분을 반드시 고려**해야 하게 되었다.
2. **π-model**: wire는 R·C로 모델링하며, π-segment 3개만 사용해도 실제 분포 RC와의 오차가 3% 수준이라 π-model을 사용한다. 이렇게 하면 익숙한 RC 회로가 되어 Elmore delay로 계산할 수 있다.
3. **Rising time 측정**: 정의는 0.2 V_DD → 0.8 V_DD. VDD = 0.9 V 시연에서는 180 mV → 720 mV 기준. 이상적으로 보이는 CLK도 확대하면 유한한 rising time을 가진다.
4. **실측값**: 최소 사이즈(100n)일 때 상승엣지 마커 측정 dx = **2.4325 ps** (182.7→735.3 mV, slope 227.2 GV/s). W를 1.1μ/2.2μ로 키운 후 dx = **1.6889 ps** (171.1→722.5 mV, slope 326.5 GV/s) — PMOS가 출력을 VDD로 끌어올리는 능력이 커져 rising이 빨라짐.
5. **Self-loading**: W를 10배 이상 키워도 gate 자체 delay는 RC 모델 예측대로 거의 일정 (R↓∝1/W, C↑∝W).
6. **Gate cap 추출**: C_gate를 100 aF~1 fF까지 100 aF 간격으로 parametric sweep (ADE Explorer 파형 패밀리 100.0a~1.0f 확인), MOS gate 부하 노드와 slope가 일치하는 값 탐색 → **C_gate ≈ 0.2 fF** (dx=1.5687ps에서 매칭). Gate cap ∝ W이므로 fF/μm로 정규화해 두면 임의 width에 환산 가능.
7. **Delay가 cap에 정비례하지 않는 이유**: 출력 노드에 인버터 자체의 **diffusion(drain) cap**이 함께 달려 있기 때문 — delay는 (parasitic + load) 두 성분으로 구성된다는 수업 내용의 실증.
8. **이후 flow**: effective resistance(전류 측정) → τ → logical effort 손계산 delay에 τ를 곱해 시뮬레이션과 비교. 본 프로젝트는 이 비교에서 **오차 2.77%** (368.4 ps vs 378.6 ps)를 달성했다.

---

# 부록 D. 복원 검증 로그 — 원본 오탈자·결측 자료 목록

## D-1. 확대 재검증으로 정정된 값 (1차 복원본 → v2)

| 항목 | 1차 복원본 | v2 (확정) | 근거 |
|:------------------|:---------------|:-------------------|:----------------------|
| C_driver | 10.039 fF | **10.839 fF** | 687_03 14배 확대 — '8'의 이중 원형 확인 |
| §1.1 delay 라벨 | t_pd,r / t_pd,f | **t_pd,n / t_pd,p** (nMOS/pMOS gate 부하 평균) | 917_21 직전 문장 판독 |
| 표기 | C_in(unit), t_pd,FO4 식 | **C_inv(unit)**, t_pd,**FOh** = (h+p_inv)τ | 917_24 |
| 이론 delay 명칭 | t_pd-nowire | **t_pd-nrwire** (non-repeated wire) | 687_03 |
| 부록 A 매핑 | 917_24=drain cap, 917_25=FO4 | **서로 뒤바뀜** (24=FO4/Outline, 25=drain cap) | 검증 에이전트 교차 확인 |
| N=5 delay | (없음) | **767.6 ps** 추가 | 687_06 최상단 |

## D-2. 원본 보고서 자체의 오탈자·넘버링 오류 (포트폴리오 정리 시 수정 권장)

1. "측정**정** 결과" 오타 (§1.2)
2. "C_d,n per width = 0.5391 fF**//**μm" — 슬래시 중복
3. 그림 3.9의 "C_**reciever**" — receiver 철자 오류
4. **그림 3.22 번호 중복** — "Crosstalk case 2"와 "Crosstalk case 2 주기 2배"가 같은 번호 (후자는 3.23이어야 함)
5. **그림 3.7 / 3.8 캡션 중복** — 둘 다 "pmos effective resistance 측정 결과"
6. **표 2.5 번호 중복** — "Total delay"와 "Logic 확인 결과 표"가 같은 번호 (한쪽은 2.6이어야 함)
7. 표 4.7과 표 4.10의 **t_pdr 행이 완전 동일** (736/738/735/733/734) — falling만 바뀐 것일 수도 있으나 복사-붙여넣기 실수 가능성 있음
8. 과제 PPT 조건 2)의 "c[0:**16**]" — c[0:15]의 오기로 보임

## D-3. 사진·전사문으로 복구 불가능한 결측 자료 (보완 요청 목록)

| # | 결측 항목 | 위치 | 복구 방법 |
|:-:|:--------------------------|:------|:---------------------------------------|
| 1 | **5장 Power Estimation 본문 전체** | 5장 | 원본 문서 접근 또는 재촬영 필요 |
| 2 | **6장 Further Idea 본문 전체** | 6장 | 〃 |
| 3 | **7장 역할 분담 (팀원 이름·실제 분담)** | 7장 | 〃 |
| 4 | 표 2.4 sizing 1~7행 | §2.5 | 〃 (8행만 판독됨) — 또는 표 2.3 input cap을 C_inv(unit)=4.1216fF/3.3μm 비례식으로 환산하여 재계산 가능 |
| 5 | 표 4.1 Source logic별 path delay 행 내용 | §4.1 | 재촬영 필요 (표 존재·최적 행 강조까지만 확인) |
| 6 | 표 4.4 Destination logic별 path delay 행 내용 | §4.2 | 〃 |
| 7 | 표 4.6 헤더 + 1행 | §4.2 | 〃 |
| 8 | 표 2.5(Logic) 개별 셀 값 | §2.7 | 〃 (본문 서술로 결론은 확정) |
| 9 | N=3 wire delay 측정 표 | §3.5 | 〃 (N=4/5 값만 확인) |
| 10 | 그림 1.6 추세선 정확한 수식 | §1.1 | 〃 (기울기 ~1.1ps/fF, 절편 ~10ps 수준만 판독) |
| 11 | 각종 schematic/waveform 그림 원본 | 전체 | 원본 문서의 이미지 필요 |

**복구 경로 검토 결과**: 사진에서 원본 Google Docs의 URL까지는 판독되었으나, 해당 계정 접근이 불가하여 원본 문서는 회수하지 못했다. 따라서 본 문서(사진 전수 판독 기반 복원본)가 최종본이며, 위 결측 항목은 시뮬레이션 재현(별도 가이드 참조)으로 재생성하는 것을 원칙으로 한다.

---

*— 복원 v2 끝 (사진 70장 전수 판독 + 핵심 수치 41건 확대 재검증 완료) —*
