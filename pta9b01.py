#!/usr/bin/env python3
"""Read the PTA9B01 PT100 temperature through a MikroTik KNOT (Modbus TCP server).

Standard library only. Usage:
    python3 pta9b01.py 192.168.88.1
    python3 pta9b01.py 192.168.88.1 --interval 5
"""
import argparse
import socket
import struct
import sys
import time

FC_READ_HOLDING = 0x03
SCALE = 10  # register value is temperature * 10 (factor 0.1)

EXCEPTIONS = {
    1: "illegal function",
    2: "illegal data address",
    3: "illegal data value",
    4: "slave device failure",
    10: "gateway path unavailable",
    11: "gateway target device failed to respond",
}


def recv_exact(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("connection closed by the KNOT")
        data += chunk
    return data


def read_register(host, port, unit, register, tid, timeout):
    # MBAP header: transaction id, protocol id (0), length, unit id
    # PDU: function code, start address, quantity
    request = struct.pack(">HHHBBHH", tid, 0, 6, unit, FC_READ_HOLDING, register, 1)

    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall(request)
        header = recv_exact(sock, 7)
        r_tid, _, length, _ = struct.unpack(">HHHB", header)
        body = recv_exact(sock, length - 1)

    if r_tid != tid:
        raise ValueError(f"transaction id mismatch: sent {tid}, got {r_tid}")

    function = body[0]
    if function & 0x80:
        code = body[1]
        raise RuntimeError(f"Modbus exception {code}: {EXCEPTIONS.get(code, 'unknown')}")

    byte_count = body[1]
    if function != FC_READ_HOLDING or byte_count != 2:
        raise ValueError(f"unexpected response: function {function}, byte count {byte_count}")

    # Signed 16-bit, big-endian
    return struct.unpack(">h", body[2:4])[0]


def format_temp(raw):
    return f"{raw / SCALE:.1f} C"


def main():
    parser = argparse.ArgumentParser(description="Read PTA9B01 temperature via KNOT Modbus TCP")
    parser.add_argument("host", help="IP address of the KNOT")
    parser.add_argument("--port", type=int, default=502, help="Modbus TCP port (default 502)")
    parser.add_argument("--unit", type=lambda s: int(s, 0), default=1,
                        help="slave ID of the sensor (default 1)")
    parser.add_argument("--register", type=lambda s: int(s, 0), default=0,
                        help="holding register address (default 0x0000)")
    parser.add_argument("--timeout", type=float, default=2.0, help="seconds (default 2)")
    parser.add_argument("--interval", type=float, default=0,
                        help="repeat every N seconds, 0 reads once (default 0)")
    args = parser.parse_args()

    tid = 1
    try:
        while True:
            try:
                raw = read_register(args.host, args.port, args.unit, args.register,
                                    tid, args.timeout)
                stamp = time.strftime("%H:%M:%S")
                print(f"{stamp}  raw={raw:6d}  temperature={format_temp(raw)}")
            except socket.timeout:
                print("no response (timeout): check power, A/B wiring and slave ID",
                      file=sys.stderr)
            except ConnectionRefusedError:
                print("connection refused: check that /iot modbus is enabled on the KNOT",
                      file=sys.stderr)
            except OSError as err:
                print(f"network error: {err}", file=sys.stderr)
            except (RuntimeError, ValueError, ConnectionError) as err:
                print(f"error: {err}", file=sys.stderr)

            if args.interval <= 0:
                break
            tid = (tid % 65535) + 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
