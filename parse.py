import discord
from discord import utils

def parse(champions, levels, timers, emojis):
    message = ""
    for champion in champions:
        message += "**" + champion + "** (lvl. " + str(levels[champion]) + ")\n" 
        if (champion, "Flash") in timers:
           message += str(discord.utils.get(emojis, name = "Flash")) + " " + str(int(timers[(champion, "Flash")])) + "\t\t"
        for (c, ability) in timers:
            if champion == c and ability != "R" and ability !="Flash":
               message += str(discord.utils.get(emojis, name = ability))+ " " + str(int(timers[(champion, ability)])) + "\t\t"
        if (champion, "R") in timers:
            message += "**R** " + str(int(timers[(champion, "R")]))
        message += "\n\n"
    return message
