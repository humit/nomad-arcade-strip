
Game Spec
Game name

Nomad Arcade Strip / Color Shooter

Display

1D WS2812B LED strip.

Current debug/play length:

150 LEDs

Planned variants:

150 LEDs
300 LEDs
Player-side UI
LED 0-4    base/player zone
LED 5      danger marker
LED 6-9    special charge / ready indicator
LED 10-12  reserved/debug, normally off
LED 13+    playfield
Enemy types
green   killed by green shot
red     killed by red shot
yellow  wildcard, killed by either green or red
Boss concept

A boss is a multi-color creature represented by a visible color sequence.

Examples:

green, green
red, red
yellow, red, red
green, red, green

The player must fire the matching sequence. Yellow boss segments accept either green or red.

Later bosses may require multiple phases, color changes, or unlocked weapons.

Input actions

The game should use abstract actions, not direct button logic:

GREEN_FIRE
RED_FIRE
SPECIAL
PAUSE
MENU_SELECT

Physical buttons, gamepads, and phone/web controls should all map into these actions.
