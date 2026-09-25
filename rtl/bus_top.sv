// -----------------------------------------------------------------------------
// bus_top.sv
//
// Full 16-bit bus link: source -> bus wires -> destination.
//
// The physical link between the two blocks is a 200 um metal line whose RC is
// significant: unrepeated, it adds ~600 ps of Elmore delay on top of the
// ~379 ps logic path. Repeater insertion (N = 4 segments) brings the measured
// end-to-end delay from 1030.5 ps down to 762.2 ps, and wire-aware re-sizing
// of the two ends reaches 756.4 ps. See the report (디지털전자회로_Project_보고서.md), Ch. 3 and Ch. 4.
//
// At RTL the wire is a plain connection; the delay work lives in the
// transistor-level design and in tools/wire_analysis.py.
// -----------------------------------------------------------------------------

`default_nettype none

module bus_top #(
    parameter int unsigned WIDTH = 16,
    localparam int unsigned SEL_W = $clog2(WIDTH)
) (
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    input  wire [SEL_W-1:0] sel,
    output wire             d,
    output wire             all_equal
);

  wire [WIDTH-1:0] y;

  bus_source #(
      .WIDTH(WIDTH)
  ) u_source (
      .a        (a),
      .b        (b),
      .y        (y),
      .all_equal(all_equal)
  );

  // Bus metal line. Physically this is the repeated 200 um interconnect
  // characterized in Ch. 3; functionally it is transparent.
  wire [WIDTH-1:0] y_bus;
  assign y_bus = y;

  bus_destination #(
      .WIDTH(WIDTH)
  ) u_destination (
      .y  (y_bus),
      .sel(sel),
      .d  (d)
  );

endmodule

`default_nettype wire
