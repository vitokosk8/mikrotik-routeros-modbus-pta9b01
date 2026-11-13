# MQTT setup for the PTA9B01 publisher (MikroTik KNOT, RouterOS 7)
#
# Adjust the broker address to the IP of your Mosquitto container.
# Requires the temp-mqtt script (temp-mqtt.rsc) to exist first.

/iot mqtt brokers add name=mosquitto address=172.16.76.6 port=1883 auto-connect=yes
/iot mqtt connect broker=mosquitto

# Publish every 30 seconds
/system scheduler add name=temp-mqtt-sched interval=30s on-event=temp-mqtt
