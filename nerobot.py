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
    'noplaylist': True
}

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
client = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready():
    music_activities = [
        "lofi beats",
        "jazz classics",
        "chill vibes",
        "indie tracks",
        "relaxing tunes",
        "soulful sounds",
        "instrumental tracks",
        "classical symphonies",
        "acoustic jams",
        "electronic beats",
        "the latest releases",
        "90's hits",
        "reggae vibes",
        "some vinyls",
        "smooth jazz",
        "dance hits",
        "garage tunes",
        "happy tunes",
        "ambient sounds",
        "funk grooves",
        "some mixtapes"
    ]
    activity = random.choice(music_activities)
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=activity))
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('----------------------------------------------------')

class MusicBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = []
        self.last_now_playing_msg_id = None
        self.current_song = None

    @commands.command()
    async def play(self, ctx, *, search):
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send("## **You're not in a voice channel **❌")

        if not ctx.voice_client:
            await voice_channel.connect()

        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                url = info['url']
                title = info['title']
                self.queue.append((url, title))
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

            print(f"Playing: {self.current_song}")  # Debugging print

            # Delete the last "Now Playing" message if it exists
            if self.last_now_playing_msg_id:
                try:
                    # Try to fetch and delete the last "Now Playing" message
                    last_msg = await ctx.channel.fetch_message(self.last_now_playing_msg_id)
                    await last_msg.delete()
                    print("Deleted last 'now playing' message.")  # Debugging print
                except discord.NotFound:
                    # If the message is not found, just pass
                    print("Last 'now playing' message not found; no deletion needed.")  # Debugging print
                    pass

            # Send a new "Now Playing" message
            new_msg = await ctx.send(f'## **Now Playing **🎵 \n > **{title}**')
            self.last_now_playing_msg_id = new_msg.id  # Store the ID of the new message
            print("Sent new 'now playing' message.")  # Debugging print

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            await ctx.send("## **Current track has been skipped **⏩")
            ctx.voice_client.stop()
            print("The current track has been skipped.")

    @commands.command()
    async def queue(self, ctx):
        if not ctx.voice_client.is_playing():
            await ctx.send("## **NeroBot's queue is currently empty **🪹")
            print("The queue was requested to be displayed but was empty.")
        elif ctx.voice_client.is_playing() and not self.queue:
            queueString = f"## **Currently Playing** 🎵\n> **{self.current_song}**\n\n## **Up Next** ↩️\n..."
            await ctx.send(queueString)
            print("The queue has been displayed.")
        else:
            # Format currently playing track and queue list separately
            queueString = f"## **Currently Playing** 🎵\n> **{self.current_song}**\n\n## **Up Next** ↩️\n"
            queueString += "\n".join([f"{index + 1}. {title}" for index, (_, title) in enumerate(self.queue)])
            await ctx.send(queueString)
            print("The queue has been displayed.")

    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("## **NeroBot has disconnected from the voice channel **👋")
            print("Bot has been disconnected")

    @commands.command()
    async def clear(self, ctx):
        self.queue.clear()
        await ctx.send("## **The track queue has been cleared **🗑️")
        print("The track queue has been cleared")

    @commands.command()
    async def goodbot(self, ctx):
        author = ctx.author.voice.channel
        await ctx.send(f'## **Thanks {author} ** 🥰')
        print("Bot has been thanked")

    @commands.command()
    async def about(self, ctx):
        await ctx.send("# About NeroBot :robot:\n- NeroBot is a youtube-based discord music bot written in Python and is about ~200 lines of code. \n - It uses the following libraries: yt_dlp, discord.py, dotenv, and some other internal libraries.\n- NeroBot runs on a Raspberry Pi 3.0 B+ single core machine (WIP).\n- You can access the git repository and view the development timeline [here](https://github.com/JorenDryden/nerobot).")
        print("Printed about message")

    @commands.command()
    async def commands(self, ctx):
        commandList = """ 
        ## __**NeroBot Commands**__📋\n- **!play <title>** - play a track from youtube\n- **!skip** - skip the current track\n- **!queue** - view the current track queue \n- **!clear** - clears the queue of all tracks\n- **!leave** - disconnects NeroBot\n- **!commands** -  display all relevant commands\n- **!goodbot** - thank the bot for its service\n- **!about** - about NeroBot"""
        await ctx.send(commandList)
        print("Printed commands list.")

async def main():
    await client.add_cog(MusicBot(client))
    await client.start(api_token)

asyncio.run(main())
