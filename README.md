NEORV32 integration test with LiteX.

**2022-02-17: Now directly integrated in LiteX!**

[> Run Simulation
-----------------
````
$ litex_sim --cpu-type=neorv32
````

[> Build/Run it on Nexys-Video
------------------------------
````
$ python3 -m litex_boards.targets.digilent_nexys_video --cpu-type=neorv32 --uart-name=usb_fifo --build --load
````
