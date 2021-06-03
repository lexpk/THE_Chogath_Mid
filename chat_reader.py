import pyautogui
import pytesseract
import cv2
import numpy as np
import functools
import re
from PIL import Image

import loldata

CHATWINDOW_X_START = 200
CHATWINDOW_X_END = 600
CHATWINDOW_Y_START = 690
CHATWINDOW_Y_END = 860

champions           = loldata.champions()
summonerspells      = loldata.summonerspells()
matcheschamp        = "("  + (')|('.join(map((lambda x : re.escape(x)), list(champions)))).replace("'", "\\'") + ")"
matchessummoner     = "("  + (')|('.join(map((lambda x : re.escape(x)), list(summonerspells)))) + ")"
champ_is_alive      = re.compile("(?P<champion>(" + matcheschamp + "))( - Alive)")
champ_level         = re.compile("(?P<champion>(" + matcheschamp + "))( - Level )(?P<level>\d+)")
champ_summonerspell = re.compile("(?P<champion>(" + matcheschamp + ")) (?P<summoner>(" + matchessummoner + "))")
champ_ult           = re.compile("(?P<champion>(" + matcheschamp + ")) R")

def parse(chat):
    chat = chat.replace("|", "1")
    chat = chat.replace("Usdyr", "Udyr")
    chat = chat.replace("’", "'")
    print(chat)
    alive_events, level_events, summonerspell_events, ult_events = [], [], [], []
    for line in chat.splitlines():
        m = re.match(champ_is_alive, line)
        if m:
            alive_events.append(m.groupdict())
            continue
        m = re.match(champ_level, line)
        if m:
            level_events.append((m.groupdict()))
            continue
        m = re.match(champ_summonerspell, line)
        if m:
            summonerspell_events.append(m.groupdict())
            continue
        m = re.match(champ_ult, line)
        if m:
            ult_events.append(m.groupdict())
            continue
    return (alive_events, level_events, summonerspell_events, ult_events)

def get_events(debug=False, from_example=False):
    if debug and from_example:
        image = Image.open('debug\images\example.png')
    else:
        image = pyautogui.screenshot()
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)[CHATWINDOW_Y_START:CHATWINDOW_Y_END,
                                                             CHATWINDOW_X_START:CHATWINDOW_X_END]
   
    enemy_name = cv2.inRange(image, np.array([20, 20, 160]), np.array([80, 80, 256]))
    enemy_spell = cv2.inRange(image, np.array([0, 140, 180]), np.array([40, 180, 256]))
    enemy_status = cv2.inRange(image, np.array([150, 200, 160]), np.array([210, 255, 200]))
    filtered_image = cv2.bitwise_or(cv2.bitwise_or(enemy_name, enemy_spell), enemy_status)
    filtered_image = functools.reduce((lambda a,b : cv2.bitwise_or(a, b)), [enemy_name, enemy_spell],  enemy_status)

    if debug:
        cv2.imwrite('debug/images/image.png', image)
        cv2.imwrite('debug/images/enemy_name.png', enemy_name)
        cv2.imwrite('debug/images/enemy_spell.png', enemy_spell)
        cv2.imwrite('debug/images/enemy_status.png', enemy_status)
        cv2.imwrite('debug/images/filtered_image.png', filtered_image)
    
    try:
        chat = pytesseract.image_to_string(filtered_image, timeout = 0.5)
    except pytesseract.TesseractError:
        return ([], [], [], [])
    return parse(chat)

def update_enemies(enemies):
    for eventtype in get_events():
        for event in eventtype:
            if not event["champion"] in enemies:
                enemies.append(event["champion"])

def update_timers_and_levels(timers, levels, new_cd_delay, cd_timestep):
    (alive_events, level_events, summonerspell_events, ult_events) = get_events()
    for event in level_events:
        levels[event["champion"]] = int(event["level"])
    for event in summonerspell_events:
        if not (event["champion"], event["summoner"]) in timers or timers[event["champion"], event["summoner"]] < 30:
            if event["summoner"] == "Teleport":
                timers[event["champion"], event["summoner"]] = 430.588 - 10.588*levels[event["champion"]] - new_cd_delay
            else:
                timers[event["champion"], event["summoner"]] = summonerspells[event["summoner"]][0] - new_cd_delay
    for event in ult_events:
        if not (event["champion"], "R") in timers or timers[(event["champion"], "R")] < 30:
            if levels[event["champion"]] < 11:
                timers[(event["champion"], "R")] = champions[event["champion"]][0] - new_cd_delay
                continue
            if levels[event["champion"]] < 16:
                timers[(event["champion"], "R")] = champions[event["champion"]][1] - new_cd_delay
                continue
            else:
                timers[(event["champion"], "R")] = champions[event["champion"]][2] - new_cd_delay
                continue
    finished = []
    for t in timers:
        timers[t] -= cd_timestep
        if timers[t] < 0:
            finished.append(t)
    for t in finished:
        timers.pop(t)
