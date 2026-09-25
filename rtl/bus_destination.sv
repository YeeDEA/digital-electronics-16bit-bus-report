// -----------------------------------------------------------------------------
// bus_destination.sv
//
// Destination side of the 16-bit bus: a WIDTH-to-1 multiplexer.
//
// The transistor-level version (the report (디지털전자회로_Project_보고서.md), Ch. 2 and Ch. 4) is built from
// two cascaded 4:1 MUX stages, each a NAND3 + NAND4 pair. That structure was
// selected over compound-gate and tri-state alternatives because a NAND-based
// MUX avoids the tall series stacks those styles require:
//
//   g_compound = g_tristate = 2.00   vs   g_nand2mux = 1.78
//
// Ch. 4 revisits the choice: a NAND5-based MUX had a lower predicted path
// delay but simulated slower, because logical effort does not capture the
// slew and charge-sharing penalties of a 5-deep series stack.
// -----------------------------------------------------------------------------

`default_nettype none

module bus_destination #(
    parameter int unsigned WIDTH = 16,
    localparam int unsigned SEL_W = $clog2(WIDTH)
) (
    input  wire [WIDTH-1:0] y,
    input  wire [SEL_W-1:0] sel,
    output wire             d
);

  assign d = y[sel];

endmodule

`default_nettype wire
