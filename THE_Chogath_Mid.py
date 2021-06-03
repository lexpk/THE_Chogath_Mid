import os
from dotenv import load_dotenv
import asyncio
import discord

import chat_reader
import parse

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
client = discord.Client()

flag = False

async def go():
    global flag
    channel = client.get_channel(int(os.getenv('CHANNEL_ID')))
    enemies = []
    async def update_enemies():
        chat_reader.update_enemies(enemies)
    while flag and len(enemies) < 5:
        await update_enemies()
        await asyncio.sleep(1)
    else:
      if len(enemies) < 5:
          return
    timers = dict()
    levels = { c : 1 for c in enemies }
    message = await channel.send(parse.parse(enemies, levels, timers, client.emojis))
    async def update_timers_and_levels(prev, curr):
        chat_reader.update_timers_and_levels(timers, levels, 20, curr - prev)
        await message.edit(content=parse.parse(enemies, levels, timers, client.emojis))
    curr = client.loop.time()
    while flag:
        prev = curr
        curr = client.loop.time()
        await update_timers_and_levels(prev, curr)
        await asyncio.sleep(1)
    else:
        await message.delete()

@client.event
async def on_message(message):
    if message.channel.id == int(os.getenv('CHANNEL_ID')):
        if message.author == client.user:
                return 
        global flag
        await message.delete()
        if flag and message.content == "!stop":
            flag = False
        if not flag and message.content == "!start":
            flag = True
            await go()

client.run(TOKEN)
