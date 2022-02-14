NEORV32 integration test with LiteX.

[> Run Simulation
-----------------
````
$ litex_sim --cpu-type=neorv32 --opt-level=O0 --trace
vcd2fst -v build/sim/gateware/sim.vcd -f sim.fst
gtkwave sim.fst
````
