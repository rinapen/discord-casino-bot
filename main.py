import config
from bot import bot
import commands 
import asyncio

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

async def keep_alive():
    while True:
        await asyncio.sleep(1800)
        await bot.tree.sync()

bot.loop.create_task(keep_alive())

bot.run(config.TOKEN)