# Module3_leg
This repo holds the master(Raspberry Master) and slave(Teensy Slave) code for module3 legs

When running Raspberry Master on Raspberry Pi make sure to enable i2c:

 Using raspi-config (Recommended)

    Open the terminal on your Raspberry Pi.
    Run the configuration tool: sudo raspi-config.
    Navigate to Interfacing Options (or Advanced Options) > I2C.
    When asked, select Yes to enable the ARM I2C interface.
    Select Finish and choose Yes to reboot when prompted

before running make sure Teensy Slave(2) and Raspberry Master are connected to the Module 3 structure

Error codes I/O error and Input/Output error are errors due to the teensy connections 