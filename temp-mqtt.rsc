# PTA9B01 temperature publisher for MikroTik KNOT (RouterOS 7)
#
# Reads holding register 0x0000 from slave 0x01 over Modbus RTU, decodes it
# as a signed 16-bit value in 0.1 degrees Celsius and publishes it as plain
# text to the MQTT topic knot/pta9b01/temp through the broker "mosquitto".
#
# Setup: see mqtt-setup.rsc
# Run:   /system script run temp-mqtt

:local raw [/iot modbus read-holding-registers slave-id=0x01 num-regs=0x1 reg-addr=0x0 as-value once];
:local v [:tonum ($raw->"values")];

# Two's complement: values above 32767 are negative (see protocol manual)
:if ($v > 32767) do={:set v ($v - 65536)};

# Work with the absolute value and keep the sign separately
:local sign "";
:if ($v < 0) do={:set sign "-"; :set v (-$v)};

# Integer arithmetic only: RouterOS parses 0.1 as an IP address
:local t ($v / 10);
:local d ($v - $t * 10);

/iot mqtt publish broker=mosquitto topic="knot/pta9b01/temp" message=($sign . $t . "." . $d)
