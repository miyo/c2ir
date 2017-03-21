`default_nettype none
  
module firefly_led_sim;
   
   reg clk   = 1'b0;
   reg reset = 1'b0;
   reg [31:0] counter = 32'h0;
   
   wire[7:0] led_out;
   wire led = led_out[0];
   
   firefly_led u(
	  .clk(clk),
	  .reset(reset),
	  .led_in(8'd0),
	  .led_we(1'b0),
	  .led_out(led_out),
	  .firefly_led_a(32'd0),
	  .firefly_led_b(32'd0),
	  .firefly_led_busy(),
	  .firefly_led_req(1'b0),
	  .firefly_led_test_busy(),
	  .firefly_led_test_req(1'b1)
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
