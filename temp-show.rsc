# PTA9B01 PT100 temperature reader for MikroTik KNOT (RouterOS 7)
#
# Reads holding register 0x0000 from slave 0x01 over Modbus RTU,
# treats it as a signed 16-bit value scaled by 0.1 degrees Celsius,
# and prints the result to the console.
#
# Usage:
#   /system script add name=temp-show source="<paste the command below>"
#   /system script run temp-show

:local raw [/iot modbus read-holding-registers slave-id=0x01 num-regs=0x1 reg-addr=0x0 as-value once];
:local v [:tonum ($raw->"values")];

# Convert unsigned 16-bit to signed
:if ($v > 32767) do={:set v ($v - 65536)};

# Integer arithmetic only: RouterOS parses 0.1 as an IP address
:local t ($v / 10);
:local d ($v - $t * 10);

:put ("PTA9B01: " . $t . "." . $d . " C");