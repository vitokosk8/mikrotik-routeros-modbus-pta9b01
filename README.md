# Reading a PT100 temperature sensor over Modbus RTU with a MikroTik KNOT

Small notes and a working RouterOS script for reading a PTA9B01 PT100 RS-485
temperature probe connected to a MikroTik KNOT (RouterOS 7).

## Modbus in brief

Modbus is a request/response protocol for industrial devices. A master (here,
the KNOT) sends a request and a slave (the sensor) replies. Data lives in
16-bit registers, each identified by an address.

- **Modbus RTU** runs over serial lines such as RS-485 (two wires, A+ and B-).
- **Modbus TCP** carries the same frames over Ethernet, port 502.
- **Function codes** define the operation. This project uses:
  - `0x03` read holding registers
  - `0x06` write single holding register (not used here, it changes the sensor configuration)
- **Slave ID** (unit ID) is the device address on the bus, from 1 to 247.

Values are integers. Decimal numbers, negative values and 32-bit floats must
be decoded by the reader using the device's register map.

## Hardware

| Item | Details |
|---|---|
| Router | MikroTik KNOT (RB924iR-2nD-BT5&BG77), RouterOS 7.25.1 |
| Sensor | Eletechsup PTA9B01, PT100 RS-485 acquisition module |
| Power | 8-25 V DC (12 V recommended) |
| Serial | 9600 baud, 8N1 (default for the sensor) |
| Probe wiring | 3-wire (remove the jumper) or 2-wire (jumper closed) |

Wiring: connect A+ and B- from the sensor to the KNOT RS-485 terminal. Swapping
A and B prevents communication.

## Configuration on the KNOT

```
/port print
# port "modbus" must show USED-BY modbus and BAUD-RATE 9600

/iot modbus set disabled=no
/iot modbus print
```

## Verifying communication

A single holding-register read:

```
:put [/iot modbus read-holding-registers slave-id=0x01 num-regs=0x1 reg-addr=0x0 as-value once]
```

Raw frame check with `transceive` (function 3, register 0, one register):

```
/iot modbus transceive address=1 function=3 data=00000001
```

A successful reply looked like this:

```
data: 0103020112
values: 274
status: ok
```

Frame layout: `01` address, `03` function, `02` byte count, `0112` the register value.

## What we found

- Register `0x0000` is the temperature.
- Scale factor is **0.1**: raw `274` is `27.4 °C`.
- Verified by rubbing the probe with fingers. The raw value rose gradually from
  274 to 348, which means 27.4 °C to 34.8 °C, a plausible range for that action.
- It has not yet been compared against a calibrated reference thermometer.

## Script

[`temp-show.rsc`](temp-show.rsc) reads register 0, converts the value to
signed, scales it and prints it to the console.

```
/system script add name=temp-show source="..."   # or paste the file content
/system script run temp-show
```

Output:

```
PTA9B01: 27.4 C
```

The conversion uses integer arithmetic only. RouterOS reads `0.1` as an IP
address, so `value * 0.1` fails with "cannot multiply integer number by ip
address". Integer division and remainder avoid that problem.

## Known limitations

- Negative temperatures are not tested. The decimal part is computed as
  `v - t * 10`, which can give odd output for negative values.
- Register `0x0001` has not been identified.
- The sensor's default slave ID was assumed to be `0x01`; it works, but the
  manufacturer's protocol sheet was not found.
- The temperature correction register, if any, was not checked.

## Next steps

1. Compare readings with a reference thermometer to check accuracy.
2. Read the second register and identify it (resistance or second channel).
3. Test negative values in a cold environment.
4. Add a threshold alarm on a GPIO pin, or log readings with the scheduler.

## Sources

- MikroTik RouterOS manual, Modbus: https://manual.mikrotik.com/docs/internet-of-things/modbus/
- Eletechsup PTA9B01 product listing (interface and range details)