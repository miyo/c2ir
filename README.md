# c2ir

A test project to generate Synthesijer-IR from C codes.

This project requires pycparser(https://github.com/eliben/pycparser) and Python3.
If you want to test by using examples/Makefile, Synthesijer and Icarus-Verilog are also required to compile Synthesijer-IR into VerilogHDL/VHDL and run simulation.

## Pre-Requirements:

- Python3.x
- pycparser https://github.com/eliben/pycparser

Synthesijer is also required to compile Synthesijer-IR into VHDL/VerilogHDL.
- Synthesijer http://synthesijer.github.io/web/

## Examples:

    cd examples
    make
    ./firefly_led_sim
    gtkwave firefly_led_sim.vcd

