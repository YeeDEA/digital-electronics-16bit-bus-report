// -----------------------------------------------------------------------------
// tb_bus.sv
//
// Self-checking testbench: bus_top (RTL) against bus_ref_model (independent,
// bit-serial model written from the spec text). Every vector compares both
// outputs, d and all_equal.
//
//   1. Directed: a == b for corner words, every select line.
//   2. Directed: a single mismatching bit at each position, every select line
//      (the 1's detector must close the gate for any one disagreement).
//   3. Random: N_RAND vectors, half forced to a == b so the gate actually opens.
//
// Exit: prints "PASS <n> vectors" or "FAIL <k> mismatches"; $fatal on failure.
// -----------------------------------------------------------------------------

`timescale 1ns/1ps
`default_nettype none

module tb_bus;
  localparam integer WIDTH  = 16;
  localparam integer SEL_W  = 4;
  localparam integer N_RAND = 20000;

  reg  [WIDTH-1:0] a, b;
  reg  [SEL_W-1:0] sel;
  wire             d_dut, eq_dut;
  wire             d_ref, eq_ref;

  bus_top       #(.WIDTH(WIDTH)) dut (.a(a), .b(b), .sel(sel), .d(d_dut), .all_equal(eq_dut));
  bus_ref_model #(.WIDTH(WIDTH)) ref_m (.a(a), .b(b), .sel(sel), .d(d_ref), .all_equal(eq_ref));

  integer n_vec = 0;
  integer n_bad = 0;
  integer i, s, k;
  reg [WIDTH-1:0] corners [0:5];

  task check;
    begin
      #1;
      n_vec = n_vec + 1;
      if (d_dut !== d_ref || eq_dut !== eq_ref) begin
        n_bad = n_bad + 1;
        if (n_bad <= 10)
          $display("MISMATCH a=%h b=%h sel=%0d : dut d=%b eq=%b | ref d=%b eq=%b",
                   a, b, sel, d_dut, eq_dut, d_ref, eq_ref);
      end
    end
  endtask

  initial begin
    corners[0] = 16'h0000; corners[1] = 16'hFFFF; corners[2] = 16'hAAAA;
    corners[3] = 16'h5555; corners[4] = 16'h8001; corners[5] = 16'h7FFE;

    // 1. equal words, every select
    for (k = 0; k < 6; k = k + 1)
      for (s = 0; s < WIDTH; s = s + 1) begin
        a = corners[k]; b = corners[k]; sel = s; check;
      end

    // 2. one mismatching bit at each position, every select
    for (k = 0; k < 6; k = k + 1)
      for (i = 0; i < WIDTH; i = i + 1)
        for (s = 0; s < WIDTH; s = s + 1) begin
          a = corners[k]; b = corners[k] ^ (16'h1 << i); sel = s; check;
        end

    // 3. random, half with a == b
    for (k = 0; k < N_RAND; k = k + 1) begin
      a   = $random;
      b   = (k % 2 == 0) ? a : $random;
      sel = $random;
      check;
    end

    if (n_bad == 0) $display("PASS %0d vectors", n_vec);
    else begin
      $display("FAIL %0d mismatches out of %0d vectors", n_bad, n_vec);
      $fatal(1, "RTL does not match the reference model");
    end
    $finish;
  end
endmodule

`default_nettype wire
