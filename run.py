import discord
import os
import asyncio
import random
import time

from nerobot import MusicBot
from dotenv import load_dotenv
from discord.ext import commands
from colorama import Fore, init

load_dotenv()
api_token = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

init(autoreset=True)
systemColor = Fore.LIGHTBLUE_EX
userInputColor = Fore.LIGHTGREEN_EX
statusColor = Fore.CYAN
userColor = Fore.LIGHTMAGENTA_EX
addedToQueue = Fore.LIGHTYELLOW_EX

client = commands.Bot(command_prefix="!", intents=intents)
app = MusicBot(client)

async def main():
    async def setup_hook():
        await client.add_cog(app)
    client.setup_hook = setup_hook
    await client.start(api_token)

@client.event
async def on_ready():
    print(f'Logged in as {statusColor}{client.user} (ID:{client.user.id})')
    print('--------------------------------------------------')
    asyncio.create_task(auto_disconnect(app))  # Create task for auto disconnect
    asyncio.create_task(update_presence())  # Create task for updating presence

async def update_presence():
    music_activities = [
        "lofi beats", "jazz classics", "chill vibes", "indie tracks",
        "relaxing tunes", "soulful sounds", "instrumental tracks",
        "classical symphonies", "acoustic jams", "electronic beats",
        "the latest releases", "90's hits", "reggae vibes",
        "some vinyls", "smooth jazz", "dance hits", "garage tunes",
        "happy tunes", "ambient sounds", "funk grooves", "some mix-tapes",
        "leighton scream", "tiktok mic-spam", "girl-pop",
    ]
    while True:
        activity = random.choice(music_activities)
        await client.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name=activity)
        )
        await asyncio.sleep(60 * 30)  # Update presence every 30 minutes

async def auto_disconnect(app):
    await client.wait_until_ready()
    while True:
        for vc in client.voice_clients:
            if not vc.is_playing() and not app.is_paused:
                print(f'{systemColor}[System] - [{time.ctime()}] - Starting auto disconnect sequence')
                await asyncio.sleep(600)
                if not vc.is_playing():
                    print(f'{systemColor}[System] - [{time.ctime()}] - Bot has been auto disconnected')
                    await vc.disconnect()
                else:
                    print(f'{systemColor}[System] - [{time.ctime()}] - Cancelled auto disconnect sequence')
        await asyncio.sleep(60)

asyncio.run(main())