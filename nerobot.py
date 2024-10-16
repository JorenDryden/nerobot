import time
import discord
from discord.ext import commands
import random
import yt_dlp
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve the Discord token from environment variable
api_token = os.getenv("DISCORD_TOKEN")
if api_token is None:
    raise ValueError("DISCORD_TOKEN is not set or could not be loaded.")

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YDL_OPTIONS = {
    'format': 'bestaudio',
    'noplaylist': True,
    'quiet': True
}

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
client = commands.Bot(command_prefix="!", intents=intents)



@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('---------------------------------------------------')
    # Start the periodic update loop when bot is ready
    client.loop.create_task(periodic_update())

async def update_presence():
    music_activities = [
        "lofi beats", "jazz classics", "chill vibes", "indie tracks",
        "relaxing tunes", "soulful sounds", "instrumental tracks",
        "classical symphonies", "acoustic jams", "electronic beats",
        "the latest releases", "90's hits", "reggae vibes",
        "some vinyls", "smooth jazz", "dance hits", "garage tunes",
        "happy tunes", "ambient sounds", "funk grooves", "some mixtapes"
    ]
    activity = random.choice(music_activities)
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=activity))
    print(f'[System] - [{time.ctime()}] - Updated presence to: listening to {activity}')

async def periodic_update():
    while True:
        await update_presence()  # Call the presence update function
        await asyncio.sleep(20 * 60)  # Wait for 20 minute

class MusicBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = [] # The queue of all user requested tracks
        self.last_now_playing_msg_id = None # Unique ID of previous bot message (used by play_next to remove the previous message if it is identical to the newest)
        self.current_song = None # The current song playing (set by play_next() and used to update the now playing message)

    @commands.command()
    async def play(self, ctx, *, search):
        author_display_name = ctx.author.display_name
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            print(f'[System] - [{time.ctime()}] - {author_display_name} tried to summon bot but was not in a voice channel')
            return await ctx.send("## **You're not in a voice channel **❌")

        if not ctx.voice_client:
            await voice_channel.connect()
            print(f'[System] - [{time.ctime()}] - NeroBot joined "{ctx.voice_client.channel.name}" voice channel')

        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                url = info['url']
                title = info['title']
                self.queue.append((url, title))
                print(f'[User] - [{time.ctime()}] - {author_display_name} added {title} to queue')
                if ctx.voice_client.is_playing():
                    await ctx.send(f'## **Added to Queue **✅ \n> **{title}**')
                else:
                    await self.play_next(ctx)

    async def play_next(self, ctx):
        if self.queue:
            url, title = self.queue.pop(0)
            self.current_song = title  # Update current track here
            source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
            ctx.voice_client.play(source, after=lambda _: self.client.loop.create_task(self.play_next(ctx)))
            print(f"[System] - [{time.ctime()}] - Now playing: {self.current_song}")  # Debugging print
            # Delete the last "Now Playing" message if it exists
            if self.last_now_playing_msg_id:
                try:
                    # Try to fetch and delete the last "Now Playing" message
                    last_msg = await ctx.channel.fetch_message(self.last_now_playing_msg_id)
                    await last_msg.delete()
                except discord.NotFound:
                    pass

            # Send a new "Now Playing" message
            new_msg = await ctx.send(f'## **Now Playing **🎵 \n > **{title}**')
            self.last_now_playing_msg_id = new_msg.id  # Store the ID of the new message

    @commands.command()
    async def skip(self, ctx):
        author_display_name = ctx.author.display_name
        if ctx.voice_client and ctx.voice_client.is_playing():
            await ctx.send("## **Current track has been skipped **⏩")
            print(f'[User] - [{time.ctime()}] - {author_display_name} skipped {self.current_song}')
            ctx.voice_client.stop()


    @commands.command()
    async def queue(self, ctx):
        author_display_name = ctx.author.display_name
        if not ctx.voice_client.is_playing():
            await ctx.send("## **NeroBot's queue is currently empty **🪹")
            print(f'[User] - [{time.ctime()}] - {author_display_name} requested the queue but it was empty')
        elif ctx.voice_client.is_playing() and not self.queue:
            queueString = f"## **Currently Playing** 🎵\n> **{self.current_song}**\n\n## **Up Next** ↩️\n..."
            await ctx.send(queueString)
            print(f'[User] - [{time.ctime()}] - {author_display_name} requested the queue')
        else:
            # Format currently playing track and queue list separately
            queueString = f"## **Currently Playing** 🎵\n> **{self.current_song}**\n\n## **Up Next** ↩️\n"
            queueString += "\n".join([f"{index + 1}. {title}" for index, (_, title) in enumerate(self.queue)])
            await ctx.send(queueString)
            print(f'[User] - [{time.ctime()}] - {author_display_name} requested the queue')

    @commands.command()
    async def leave(self, ctx):
        author_display_name = ctx.author.display_name
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("## **NeroBot has disconnected from the voice channel **👋")
            print(f'[User] - [{time.ctime()}] - {author_display_name} disconnected NeroBot from {ctx.voice_client.channel.name}')

    @commands.command()
    async def clear(self, ctx):
        author_display_name = ctx.author.display_name
        self.queue.clear()
        await ctx.send("## **The track queue has been cleared **🗑️")
        print(f'[User] - [{time.ctime()}] - {author_display_name} displayed the current track queue')

    @commands.command()
    async def goodbot(self, ctx):
        author_display_name = ctx.author.display_name
        await ctx.send(f'## **Thanks {author_display_name} ** 🥰')
        print(f'[User] - [{time.ctime()}] - {author_display_name} thanked NeroBot')

    @commands.command()
    async def about(self, ctx):
        author_display_name = ctx.author.display_name
        await ctx.send("# About NeroBot :robot:\n- NeroBot is a youtube-based discord music bot written in Python and is about ~200 lines of code. \n - It uses the following libraries: yt_dlp, discord.py, dotenv, and some other internal libraries.\n- NeroBot runs on a Raspberry Pi 3.0 B+ single core machine (WIP).\n- You can access the git repository and view the development timeline [here](https://github.com/JorenDryden/nerobot).")
        print(f'[User] - [{time.ctime()}] - {author_display_name} displayed about me')

    @commands.command()
    async def commands(self, ctx):
        author_display_name = ctx.author.display_name
        commandList = """ 
        ## __**NeroBot Commands**__📋\n- **!play <title>** - play a track from youtube\n- **!skip** - skip the current track\n- **!queue** - view the current track queue \n- **!clear** - clears the queue of all tracks\n- **!leave** - disconnects NeroBot\n- **!commands** -  display all relevant commands\n- **!goodbot** - thank the bot for its service\n- **!about** - about NeroBot"""
        await ctx.send(commandList)
        print(f'[User] - [{time.ctime()}] - {author_display_name} displayed the command list')

async def main():
    await client.add_cog(MusicBot(client))
    await client.start(api_token)

asyncio.run(main())
