`default_nettype none
  
module firefly_led_sim;
   
   reg clk   = 1'b0;
   reg reset = 1'b0;
   reg [31:0] counter = 32'h0;
   
   wire[31:0] c_out;
   wire flag = c_out[0];
   
   firefly_led u(
	  .clk(clk),
	  .reset(reset),
	  .c_in(32'd0),
	  .c_we(1'b0),
	  .c_out(c_out),
	  .pwm_out_a(32'd0),
	  .pwm_out_b(32'd0),
	  .pwm_out_busy(),
	  .pwm_out_req(1'b0),
	  .pwm_test_busy(),
	  .pwm_test_req(1'b1)
	  );

   initial begin
      $dumpfile("firefly_led_sim.vcd");
      $dumpvars();
   end

   always #5
     clk <= !clk;

   always @(posedge clk) begin
      counter <= counter + 1;
      if(counter >= 3 && counter <= 8) begin
	 reset <= 1'b1;
      end else begin
	 reset <= 1'b0;
      end
      if(counter == 32'd10000)
	$finish;
   end
   
endmodule
`default_nettype wire
