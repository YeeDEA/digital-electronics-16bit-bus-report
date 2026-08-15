* lib_gates.sp — sized gate library for the 16-bit bus design (report tables 2.4 / 4.3 / 4.6)
* All widths in um, L = 45n. Parameter wn/wp are the per-input transistor widths.
* Include this file after .include 45nm_HP.pm

*** basic inverter (unit: wn=1.1u, wp=2.2u) ***
.subckt INV in out vdd vss wn=1.1u wp=2.2u
MP out in vdd vdd pmos W={wp} L=45n
MN out in vss vss nmos W={wn} L=45n
.ends

*** NAND2: 2 nmos series, 2 pmos parallel ***
.subckt NAND2 a b out vdd vss wn=2.2u wp=2.2u
MP1 out a vdd vdd pmos W={wp} L=45n
MP2 out b vdd vdd pmos W={wp} L=45n
MN1 out a n1  vss nmos W={wn} L=45n
MN2 n1  b vss vss nmos W={wn} L=45n
.ends

*** NAND3 ***
.subckt NAND3 a b c out vdd vss wn=3.3u wp=2.2u
MP1 out a vdd vdd pmos W={wp} L=45n
MP2 out b vdd vdd pmos W={wp} L=45n
MP3 out c vdd vdd pmos W={wp} L=45n
MN1 out a n1  vss nmos W={wn} L=45n
MN2 n1  b n2  vss nmos W={wn} L=45n
MN3 n2  c vss vss nmos W={wn} L=45n
.ends

*** NAND4 ***
.subckt NAND4 a b c d out vdd vss wn=4.4u wp=2.2u
MP1 out a vdd vdd pmos W={wp} L=45n
MP2 out b vdd vdd pmos W={wp} L=45n
MP3 out c vdd vdd pmos W={wp} L=45n
MP4 out d vdd vdd pmos W={wp} L=45n
MN1 out a n1  vss nmos W={wn} L=45n
MN2 n1  b n2  vss nmos W={wn} L=45n
MN3 n2  c n3  vss nmos W={wn} L=45n
MN4 n3  d vss vss nmos W={wn} L=45n
.ends

*** NOR2: 2 pmos series, 2 nmos parallel ***
.subckt NOR2 a b out vdd vss wn=1.1u wp=4.4u
MP1 p1  a vdd vdd pmos W={wp} L=45n
MP2 out b p1  vdd pmos W={wp} L=45n
MN1 out a vss vss nmos W={wn} L=45n
MN2 out b vss vss nmos W={wn} L=45n
.ends

*** NOR4 ***
.subckt NOR4 a b c d out vdd vss wn=1.1u wp=8.8u
MP1 p1  a vdd vdd pmos W={wp} L=45n
MP2 p2  b p1  vdd pmos W={wp} L=45n
MP3 p3  c p2  vdd pmos W={wp} L=45n
MP4 out d p3  vdd pmos W={wp} L=45n
MN1 out a vss vss nmos W={wn} L=45n
MN2 out b vss vss nmos W={wn} L=45n
MN3 out c vss vss nmos W={wn} L=45n
MN4 out d vss vss nmos W={wn} L=45n
.ends

*** 4:1 MUX built from 4x NAND3 + NAND4 (report fig 2.2) ***
* selects d0..d3 with s0,s0b,s1,s1b
.subckt MUX4 d0 d1 d2 d3 s0 s0b s1 s1b out vdd vss wn3=3.3u wp3=2.2u wn4=4.4u wp4=2.2u
X0 d0 s0b s1b m0 vdd vss NAND3 wn={wn3} wp={wp3}
X1 d1 s0  s1b m1 vdd vss NAND3 wn={wn3} wp={wp3}
X2 d2 s0b s1  m2 vdd vss NAND3 wn={wn3} wp={wp3}
X3 d3 s0  s1  m3 vdd vss NAND3 wn={wn3} wp={wp3}
XO m0 m1 m2 m3 out vdd vss NAND4 wn={wn4} wp={wp4}
.ends
