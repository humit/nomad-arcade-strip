from machine import Pin, PWM
from neopixel import NeoPixel
from time import sleep
import random

LED_PIN = 14
AUDIO_PIN = 15
AUDIO_DUTY = 12

# Two-button fallback mode:
# GPIO13 green button is disabled/broken.
# Big red physical button now fires GREEN.
# Small red physical button fires RED.
# Double-press either active button to trigger special.
BTN_GREEN = 18     # büyük kırmızı fiziksel buton -> yeşil ateş
BTN_RED = 19       # küçük kırmızı fiziksel buton -> kırmızı ateş
BTN_SPECIAL = None # ayrı special butonu yok

N = 300
BASE_SIZE = 5
MAX_LIVES = 3

DEBUG = False

# Player-side UI layout:
# 0-4   : base/player zone
# 5     : danger marker
# 6-9   : special charge/ready indicator
# 10-12 : reserved/debug only, normally off
# 13+   : playfield
SPECIAL_UI_START = 6
SPECIAL_UI_LEN = 4
DANGER_LED = 5
PLAYFIELD_START = 13

np = NeoPixel(Pin(LED_PIN, Pin.OUT), N)

btn_green = Pin(BTN_GREEN, Pin.IN, Pin.PULL_UP)
btn_red = Pin(BTN_RED, Pin.IN, Pin.PULL_UP)
btn_special = None

audio_idle = Pin(AUDIO_PIN, Pin.OUT)
audio_idle.value(0)

def clear_buf():
    for i in range(N):
        np[i] = (0, 0, 0)

def led(i, color):
    if 0 <= i < N:
        np[i] = color

def tone(freq, duration, duty=AUDIO_DUTY):
    pwm = PWM(Pin(AUDIO_PIN))
    pwm.freq(freq)
    pwm.duty(duty)
    sleep(duration)
    pwm.duty(0)
    pwm.deinit()
    audio_idle.value(0)
    sleep(0.006)

def sfx_start():
    tone(330, 0.03)
    tone(495, 0.03)
    tone(660, 0.03)
    tone(990, 0.05)

def sfx_green():
    tone(880, 0.014, 8)

def sfx_red():
    tone(440, 0.014, 8)

def sfx_hit():
    tone(660, 0.025)
    tone(990, 0.025)

def sfx_wrong():
    tone(180, 0.045)
    tone(120, 0.060)

def sfx_special():
    tone(440, 0.025)
    tone(880, 0.025)
    tone(1320, 0.05)


def sfx_level_up():
    # "dirri-dit-di-diit" ascending arcade jingle.
    tone(523, 0.035, 10)
    tone(659, 0.035, 10)
    tone(784, 0.045, 10)
    sleep(0.018)
    tone(659, 0.030, 10)
    tone(880, 0.040, 10)
    tone(1046, 0.080, 10)

def sfx_special_ready():
    # Bright, positive, short: "special is ready".
    tone(988, 0.030, 8)
    tone(1319, 0.035, 8)
    tone(1760, 0.090, 8)

def sfx_damage():
    tone(180, 0.06)
    tone(120, 0.08)

def sfx_game_over():
    tone(440, 0.05)
    tone(330, 0.06)
    tone(220, 0.10)

def fill(color):
    for i in range(N):
        np[i] = color
    np.write()

def flash(color, times=1):
    for _ in range(times):
        fill(color)
        sleep(0.05)
        fill((0, 0, 0))
        sleep(0.035)

def special_wave(state):
    normalize_enemies(state)
    # Big visible special shot: a purple/white wave travels along the strip
    # and destroys every enemy it passes.
    removed = 0
    wave_width = 10
    step = 5

    sfx_special()

    for head in range(PLAYFIELD_START, N + wave_width, step):
        # Remove enemies inside the wave window.
        kept = []
        for p, kind in state["enemies"]:
            if head - wave_width <= p <= head + 2:
                removed += 1
                # Small hit chirp, not too long.
                tone(1200, 0.006, 8)
            else:
                kept.append([p, kind])
        state["enemies"] = kept

        # Draw one special frame.
        clear_buf()

        # Base.
        for i in range(BASE_SIZE):
            led(i, (0, 12, 18))

        # Existing bullets remain visible.
        for prev, p, kind in state["bullets"]:
            if kind == 0:
                led(p, (0, 16, 0))
            else:
                led(p, (16, 0, 0))

        # Remaining enemies.
        for p, kind in state["enemies"]:
            if kind == 0:
                led(p, (0, 18, 0))
            elif kind == 1:
                led(p, (18, 0, 0))
            else:
                led(p, (18, 8, 0))
                led(p + 1, (8, 3, 0))

        # Special beam body.
        for j in range(wave_width):
            led(head - j, (12, 0, 18))

        # Bright head.
        led(head, (20, 20, 20))
        led(head - 1, (18, 0, 18))
        led(head - 2, (10, 0, 18))

        np.write()
        sleep(0.018)

    sfx_bonus_like_end()
    return removed

def sfx_bonus_like_end():
    tone(880, 0.025)
    tone(1320, 0.035)

def reset_game():
    return {
        "tick": 0,
        "score": 0,
        "lives": MAX_LIVES,
        "bullets": [],
        "enemies": [],
        "combo": 0,
        "special_energy": 40,
        "last_green": 1,
        "last_red": 1,
        "last_special": 1,
        "green_cooldown": 0,
        "red_cooldown": 0,
        "last_green_press_tick": -999,
        "last_red_press_tick": -999,
        "double_tap_window": 12,
        "last_green_press_tick": -999,
        "last_red_press_tick": -999,
        "double_tap_window": 12,
        "special_flash": 0,
        "level": 0,
        "special_ready_announced": False,
        "debug_shot": -1,
        "debug_enemy": -1,
        "debug_result": -1,
        "debug_timer": 0,
        "paused": False,
        "pause_lock": False,
    }

def draw_intro():
    clear_buf()
    for i in range(0, N, 12):
        led(i, (0, 8, 4))
        np.write()
        sleep(0.006)
    sfx_start()


def normalize_enemies(state):
    # Canonical enemy state:
    # There must be only one enemy per LED position.
    #
    # kind:
    #   0 = green
    #   1 = red
    #   2 = yellow wildcard
    #
    # If multiple enemies overlap:
    #   same color -> one enemy of that color
    #   mixed red/green/yellow -> yellow wildcard
    by_pos = {}

    for p, kind in state["enemies"]:
        if p < PLAYFIELD_START or p >= N:
            continue

        old = by_pos.get(p)

        if old is None:
            by_pos[p] = kind
        elif old == kind:
            by_pos[p] = kind
        else:
            by_pos[p] = 2

    state["enemies"] = [[p, by_pos[p]] for p in sorted(by_pos.keys())]

def spawn_enemy(state):
    normalize_enemies(state)

    # 0 = green, 1 = red, 2 = yellow wildcard
    r = random.randrange(0, 10)
    if r < 4:
        kind = 0
    elif r < 8:
        kind = 1
    else:
        kind = 2

    # Try to spawn near far end without stacking on existing enemies.
    for _ in range(12):
        pos = N - 1 - random.randrange(0, 18)

        free = True
        for ep, ek in state["enemies"]:
            if abs(ep - pos) < 4:
                free = False
                break

        if free:
            state["enemies"].append([pos, kind])
            normalize_enemies(state)
            return

    # If crowded, skip spawn this tick.
    return


def draw_pause(state):
    # Frozen game state + blinking pause marker.
    draw_state(state)

    phase = (state["tick"] // 8) % 2
    bright = (16, 16, 0)
    dim = (3, 3, 0)
    color = bright if phase == 0 else dim

    # Use reserved/debug area 10-12 and a small marker near playfield start.
    led(10, color)
    led(11, color)
    led(12, color)

    for i in range(PLAYFIELD_START, min(PLAYFIELD_START + 8, N), 3):
        led(i, color)

    np.write()

def check_pause_combo(state):
    # Pause/resume when both remaining buttons are held together.
    both_down = btn_green.value() == 0 and btn_red.value() == 0

    if both_down and not state["pause_lock"]:
        state["paused"] = not state["paused"]
        state["pause_lock"] = True

        if state["paused"]:
            tone(660, 0.04)
            tone(440, 0.06)
        else:
            tone(440, 0.04)
            tone(660, 0.06)

    if not both_down:
        state["pause_lock"] = False


def trigger_special_or_fail(state):
    if state["special_energy"] >= 100:
        use_special(state)
    else:
        sfx_wrong()

def handle_fire_button_press(state, shot_kind):
    # shot_kind: 0=green, 1=red
    # Double-tap either active button triggers special instead of normal shot.
    now = state["tick"]
    key = "last_green_press_tick" if shot_kind == 0 else "last_red_press_tick"
    last = state[key]

    is_double_tap = (now - last) <= state["double_tap_window"]
    state[key] = now

    if is_double_tap:
        trigger_special_or_fail(state)
        return

    if shot_kind == 0:
        state["bullets"].append([PLAYFIELD_START, PLAYFIELD_START, 0])
        print("SHOT kind=0 green score=%d energy=%d enemies=%s" % (state["score"], state["special_energy"], enemy_snapshot(state)))
        state["debug_shot"] = 0
        state["debug_timer"] = 12
        state["green_cooldown"] = 4
        sfx_green()
    else:
        state["bullets"].append([PLAYFIELD_START, PLAYFIELD_START, 1])
        print("SHOT kind=1 red score=%d energy=%d enemies=%s" % (state["score"], state["special_energy"], enemy_snapshot(state)))
        state["debug_shot"] = 1
        state["debug_timer"] = 12
        state["red_cooldown"] = 4
        sfx_red()

def update_buttons(state):
    check_pause_combo(state)

    g = btn_green.value()
    r = btn_red.value()

    # While paused, ignore normal fire/special inputs.
    if state["paused"]:
        state["last_green"] = g
        state["last_red"] = r
        return

    if state["green_cooldown"] > 0:
        state["green_cooldown"] -= 1
    if state["red_cooldown"] > 0:
        state["red_cooldown"] -= 1

    # GPIO18 / big red physical button now fires GREEN.
    if g == 0 and state["last_green"] == 1 and state["green_cooldown"] == 0:
        handle_fire_button_press(state, 0)

    # GPIO19 / small red physical button fires RED.
    if r == 0 and state["last_red"] == 1 and state["red_cooldown"] == 0:
        handle_fire_button_press(state, 1)

    state["last_green"] = g
    state["last_red"] = r


def use_special(state):
    state["special_energy"] = 0
    state["special_ready_announced"] = False
    state["special_flash"] = 0

    removed = special_wave(state)

    state["score"] += removed * 2
    state["combo"] += removed

def update_bullets(state):
    speed = 6
    new_bullets = []
    for prev, p, kind in state["bullets"]:
        new_p = p + speed
        if new_p < N:
            new_bullets.append([p, new_p, kind])
    state["bullets"] = new_bullets

def update_enemies(state):
    if state["tick"] % 3 != 0:
        return

    kept = []
    for p, kind in state["enemies"]:
        step = 1
        if kind == 2 and state["tick"] % 2 == 0:
            step = 2

        p -= step

        if p <= PLAYFIELD_START:
            state["lives"] -= 1
            state["combo"] = 0
            sfx_damage()
            flash((18, 0, 0), 1)
        else:
            kept.append([p, kind])

    state["enemies"] = kept
    normalize_enemies(state)


def enemy_snapshot(state, center=None, radius=12):
    # Compact list for debug: position:kind
    # kind: 0=green, 1=red, 2=yellow
    out = []
    for ep, ek in state["enemies"]:
        if center is None or abs(ep - center) <= radius:
            out.append("%d:%d" % (ep, ek))
    return ",".join(out)

def handle_collisions(state):
    normalize_enemies(state)

    bullets = state["bullets"]
    enemies = state["enemies"]

    used_bullets = set()
    used_enemies = set()

    for bi, bullet in enumerate(bullets):
        prev, bp, bkind = bullet
        lo = min(prev, bp)
        hi = max(prev, bp)

        # Find the first object hit by this bullet along its travel segment.
        # Important: a wrong-color red/green enemy blocks the bullet but does NOT die.
        best = None
        for ei, enemy in enumerate(enemies):
            ep, ekind = enemy
            if lo - 1 <= ep <= hi + 1:
                if best is None or ep < best[0]:
                    best = (ep, ei, ekind)

        if best is None:
            continue

        ep, ei, ekind = best
        used_bullets.add(bi)

        # Enemy kinds:
        #   0 = green enemy
        #   1 = red enemy
        #   2 = yellow/orange enemy, wildcard target
        #
        # Bullet kinds:
        #   0 = green shot
        #   1 = red shot
        #
        # Strict rule:
        #   green shot kills green enemy
        #   red shot kills red enemy
        #   either shot kills yellow enemy
        color_match = (bkind == ekind) or (ekind == 2)

        state["debug_shot"] = bkind
        state["debug_enemy"] = ekind
        state["debug_result"] = 1 if color_match else 0
        state["debug_timer"] = 18

        if color_match:
            used_enemies.add(ei)
            state["combo"] += 1

            points = 1 + min(state["combo"] // 4, 4)
            if ekind == 2:
                points += 2

            state["score"] += points
            state["special_energy"] = min(100, state["special_energy"] + 12 + points)
            print("KILL bullet=%d enemy=%d pos=%d score=%d energy=%d" % (bkind, ekind, ep, state["score"], state["special_energy"]))
            sfx_hit()
        else:
            # Wrong color: bullet is consumed, enemy remains.
            state["combo"] = 0
            state["special_energy"] = max(0, state["special_energy"] - 8)
            print("WRONG bullet=%d enemy=%d pos=%d score=%d energy=%d" % (bkind, ekind, ep, state["score"], state["special_energy"]))
            sfx_wrong()

    state["bullets"] = [b for i, b in enumerate(bullets) if i not in used_bullets]
    state["enemies"] = [e for i, e in enumerate(enemies) if i not in used_enemies]

def draw_state(state):
    normalize_enemies(state)
    clear_buf()

    # Base.
    for i in range(BASE_SIZE):
        led(i, (0, 12, 18))

    # Special indicator: LEDs 6-9 only.
    # Charging = blue/cyan. Ready = 4 bright purple LEDs.
    if state["special_energy"] >= 100:
        for i in range(SPECIAL_UI_LEN):
            led(SPECIAL_UI_START + i, (22, 0, 22))
    else:
        energy_len = state["special_energy"] // 25
        for i in range(min(energy_len, SPECIAL_UI_LEN)):
            led(SPECIAL_UI_START + i, (0, 8, 18))

    # Nearest enemy danger marker.
    nearest = None
    for p, kind in state["enemies"]:
        if nearest is None or p < nearest:
            nearest = p

    if nearest is not None:
        if nearest < 30:
            led(DANGER_LED, (18, 0, 0))
        elif nearest < 70:
            led(DANGER_LED, (12, 6, 0))
        else:
            led(DANGER_LED, (0, 6, 0))

    # Bullets.
    for prev, p, kind in state["bullets"]:
        if kind == 0:
            led(p, (0, 20, 0))
            led(p - 1, (0, 5, 0))
        else:
            led(p, (20, 0, 0))
            led(p - 1, (5, 0, 0))

    # Enemies.
    for p, kind in state["enemies"]:
        if kind == 0:
            led(p, (0, 18, 0))
        elif kind == 1:
            led(p, (18, 0, 0))
        else:
            led(p, (18, 8, 0))
            led(p + 1, (8, 3, 0))

    # Lives at far end.
    for i in range(state["lives"]):
        led(N - 1 - i, (18, 0, 0))

    # Score tail. Wraps every 32.
    for i in range(state["score"] % 32):
        led(N - 8 - i, (0, 0, 12))

    # Special flash.
    if state["special_flash"] > 0:
        for i in range(0, N, 20):
            led(i, (10, 0, 18))
        state["special_flash"] -= 1

    # Debug overlay is intentionally disabled during normal play.
    # LEDs 6-9 are reserved for special indicator.
    if DEBUG and state.get("debug_timer", 0) > 0:
        shot = state.get("debug_shot", -1)
        enemy = state.get("debug_enemy", -1)
        result = state.get("debug_result", -1)

        if shot == 0:
            led(10, (0, 25, 0))
        elif shot == 1:
            led(10, (25, 0, 0))

        if enemy == 0:
            led(11, (0, 25, 0))
        elif enemy == 1:
            led(11, (25, 0, 0))
        elif enemy == 2:
            led(11, (25, 25, 0))

        if result == 1:
            led(12, (0, 25, 0))
        elif result == 0:
            led(12, (25, 0, 0))

        state["debug_timer"] -= 1

    np.write()


def calc_level(score):
    if score >= 45:
        return 3
    if score >= 25:
        return 2
    if score >= 10:
        return 1
    return 0

def check_progress_audio(state):
    # Level up when score crosses the same thresholds that speed up spawning.
    new_level = calc_level(state["score"])
    if new_level > state["level"]:
        state["level"] = new_level
        sfx_level_up()

        # Visual confirmation: short cyan sweep near base.
        for head in range(PLAYFIELD_START, min(N, PLAYFIELD_START + 55), 5):
            for j in range(5):
                led(head - j, (0, 10, 18))
            np.write()
            sleep(0.010)

    # Announce special only once when it becomes ready.
    if state["special_energy"] >= 100 and not state["special_ready_announced"]:
        state["special_ready_announced"] = True
        sfx_special_ready()

def game_over_screen(score):
    sfx_game_over()
    for p in range(N - 1, -1, -10):
        clear_buf()
        for j in range(10):
            led(p - j, (18, 0, 0))
        np.write()
        sleep(0.01)

    clear_buf()
    for i in range(min(score, N)):
        led(i, (0, 0, 14))
    np.write()
    sleep(0.8)

def run():
    draw_intro()
    state = reset_game()

    while True:
        state["tick"] += 1

        spawn_interval = 24
        if state["score"] > 10:
            spawn_interval = 20
        if state["score"] > 25:
            spawn_interval = 16
        if state["score"] > 45:
            spawn_interval = 13

        update_buttons(state)

        if state["paused"]:
            draw_pause(state)
            sleep(0.05)
            continue

        if state["tick"] % spawn_interval == 0:
            spawn_enemy(state)

        update_bullets(state)
        update_enemies(state)
        handle_collisions(state)
        check_progress_audio(state)
        draw_state(state)

        if state["lives"] <= 0:
            game_over_screen(state["score"])
            draw_intro()
            state = reset_game()

        sleep(0.035)

run()
