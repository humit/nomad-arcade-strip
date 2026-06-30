import sys
import time
import serial
from pathlib import Path

if len(sys.argv) < 2:
    print("usage: python serial_log.py /dev/cu.usbserial-xxxxx [logfile]")
    sys.exit(1)

port = sys.argv[1]
logfile = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path("game_debug.log")

print(f"Opening {port}")
print(f"Logging to {logfile}")

with serial.Serial(port, 115200, timeout=0.2) as ser, logfile.open("a", encoding="utf-8") as f:
    f.write("\n\n===== LOG START %s =====\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
    f.flush()

    while True:
        data = ser.readline()
        if not data:
            continue

        text = data.decode("utf-8", errors="replace").rstrip()
        line = "%s %s" % (time.strftime("%H:%M:%S"), text)

        print(line)
        f.write(line + "\n")
        f.flush()
