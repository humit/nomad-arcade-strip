
Hardware
Current ESP32 pins
GPIO14  WS2812B DIN
GPIO15  audio PWM to PAM8403 through series resistor
GPIO18  big red physical button, temporary green fire
GPIO19  small red button, red fire
GPIO13  disabled / unreliable green button
Power

The LED strip receives 5V directly from the PSU. ESP32 and amplifier use lower-current 5V branches.

The final enclosure should keep LED power, ESP32 power, audio, button, and data connections modular and serviceable.

Notes

Development target currently uses MicroPython and a serial REPL paste uploader.
