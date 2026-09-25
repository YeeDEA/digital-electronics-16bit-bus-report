// -----------------------------------------------------------------------------
// bus_ref_model.sv
//
// Golden reference model for bus_top.
//
// Written independently of the RTL: the RTL uses vector operators (~^, &, mask)
// while this model walks the bits one at a time, straight from the spec text.
// If both agree across directed and random stimulus, a whole-vector operator
// mistake in the RTL (wrong reduction, off-by-one mask, sel truncation) has to
// show up as a mismatch rather than being mirrored by the checker.
// -----------------------------------------------------------------------------

`default_nettype none

module bus_ref_model #(
    parameter int unsigned WIDTH = 16,
    localparam int unsigned SEL_W = $clog2(WIDTH)
) (
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    input  wire [SEL_W-1:0] sel,
    output reg              d,
    output reg              all_equal
);

  integer i;
  reg [WIDTH-1:0] y;
  reg match;

  always @* begin
    // Spec: "If (a[i] == b[i]) c[i] = 1; else c[i] = 0;"
    //       "If (c[0:15] == 1) y[0:15] = a[0:15]; else y[0:15] = 0;"
    match = 1'b1;
    for (i = 0; i < WIDTH; i = i + 1) begin
      if (a[i] !== b[i]) match = 1'b0;
    end

    for (i = 0; i < WIDTH; i = i + 1) begin
      y[i] = match ? a[i] : 1'b0;
    end

    all_equal = match;
    d         = y[sel];
  end

endmodule

`default_nettype wire
