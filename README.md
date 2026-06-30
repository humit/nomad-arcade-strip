# Nomad Arcade Strip

A 1D WS2812B LED strip arcade game for ESP32/MicroPython.

Current game: Color Shooter, a red/green reflex shooter with wildcard enemies, special attack, pause mode, sound effects, and early boss mechanics.

## Current hardware

- ESP32
- WS2812B strip
- 5V PSU
- PAM8403 amplifier
- Speaker
- Push buttons

## Current firmware

Main firmware:

```text
firmware/micropython/main.py
Upload helper:

export PORT=/dev/cu.usbserial-14530
python3 tools/run_repl_file.py "$PORT" firmware/micropython/main.py
Current control mode

Temporary 2-button fallback mode:

GPIO18: green shot
GPIO19: red shot
GPIO13: disabled / broken
Special behavior is under redesign
