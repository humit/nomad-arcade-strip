import sys
import time
import serial

if len(sys.argv) != 3:
    print("usage: python run_repl_file.py PORT file.py")
    sys.exit(1)

port = sys.argv[1]
filename = sys.argv[2]

with open(filename, "rb") as f:
    code = f.read()

ser = serial.Serial(port, 115200, timeout=1)
time.sleep(0.8)

# Interrupt any running or broken code
ser.write(b"\x03")
ser.flush()
time.sleep(0.3)
ser.write(b"\x03")
ser.flush()
time.sleep(0.3)

# Enter paste mode
ser.write(b"\x05")
ser.flush()
time.sleep(0.5)

# Send slowly to avoid MicroPython REPL paste corruption
chunk_size = 24
for i in range(0, len(code), chunk_size):
    ser.write(code[i:i + chunk_size])
    ser.flush()
    time.sleep(0.015)

time.sleep(0.3)

# Finish paste mode; code executes
ser.write(b"\x04")
ser.flush()
time.sleep(1.0)

# Print response briefly
end = time.time() + 3
while time.time() < end:
    data = ser.read(1024)
    if data:
        sys.stdout.buffer.write(data)
        sys.stdout.flush()

ser.close()
