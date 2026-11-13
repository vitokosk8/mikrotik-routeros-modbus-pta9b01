# PTA9B01 temperature publisher for MikroTik KNOT (RouterOS 7)
#
# Reads holding register 0x0000 from slave 0x01 over Modbus RTU, scales it
# by 0.1 degrees Celsius and publishes the value as plain text to the MQTT
# topic knot/pta9b01/temp through the broker named "mosquitto".
#
# Setup: see mqtt-setup.rsc
# Run:   /system script run temp-mqtt

:local raw [/iot modbus read-holding-registers slave-id=0x01 num-regs=0x1 reg-addr=0x0 as-value once];
:local v [:tonum ($raw->"values")];

# Convert unsigned 16-bit to signed
:if ($v > 32767) do={:set v ($v - 65536)};

# Integer arithmetic only: RouterOS parses 0.1 as an IP address
:local t ($v / 10);
:local d ($v - $t * 10);

/iot mqtt publish broker=mosquitto topic="knot/pta9b01/temp" message=($t . "." . $d)
