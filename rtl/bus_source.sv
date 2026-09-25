// -----------------------------------------------------------------------------
// bus_source.sv
//
// Source (driver) side of the 16-bit bus.
//
//   c[i] = (a[i] == b[i])          bitwise equality -> XNOR
//   y    = (&c) ? a : '0           gate the payload on a full match
//
// The transistor-level implementation of this block is documented in
// the report (디지털전자회로_Project_보고서.md), Ch. 2. The gate-level structure chosen there after a
// logical-effort search over 15 candidate topologies was
//
//   NAND2 -> NOR2 -> NAND4 -> NOR2 -> [NAND3 -> NAND4] -> [NAND3 -> NAND4]
//
// which realizes the same function as this RTL through an 8-stage path.
// This module is the behavioral golden intent for that structure.
// -----------------------------------------------------------------------------

`default_nettype none

module bus_source #(
    parameter int unsigned WIDTH = 16
) (
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    output wire [WIDTH-1:0] y,
    output wire             all_equal
);

  // Bitwise comparison. XNOR per bit: c[i] is high when a[i] and b[i] agree.
  wire [WIDTH-1:0] c;
  assign c = ~(a ^ b);

  // 1's detector: every bit must agree before the payload is allowed through.
  assign all_equal = &c;

  // Payload gating. Replicating the enable keeps this a pure AND array, which
  // is what the transistor-level design implements (no mux, no tri-state).
  assign y = a & {WIDTH{all_equal}};

endmodule

`default_nettype wire
