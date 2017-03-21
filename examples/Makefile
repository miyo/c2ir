SYNTHESIJER ?= ../../synthesijer/bin
PYTHON ?= python3
OPT = 

all:
	$(PYTHON) ../c2ir.py arith.c
	java -cp $(SYNTHESIJER) synthesijer.Main $(OPT) --verilog arith.ir
	#iverilog -o arith_sim arith_sim.v arith.v
	$(PYTHON) ../c2ir.py cond.c
	java -cp $(SYNTHESIJER) synthesijer.Main $(OPT) --verilog cond.ir
	#iverilog -o cond_sim cond_sim.v cond.v
	$(PYTHON) ../c2ir.py firefly_led.c
	java -cp $(SYNTHESIJER) synthesijer.Main $(OPT) --verilog firefly_led.ir
	iverilog -o firefly_led_sim firefly_led_sim.v firefly_led.v

clean:
	-rm -f firefly_led.v
	-rm -f arith.v
	-rm -f cond.v
	-rm -f firefly_led_sim
	-rm -f *.o
	-rm -f *.txt
	-rm -f *.ir
	-rm -f *.dot
	-rm -f *.vcd
