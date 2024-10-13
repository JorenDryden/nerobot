import discord
from discord.ext import commands
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

class MusicBot(commands.Cog):


    def __init__(self, client):
        self.client = client
        self.queue = []
        self.current_song = None

    def getCurrentTrack(self):
        return self.__currentTrack

    def setCurrentTrack(self, track):
        self.__currentTrack = track

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

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    async def play_next(self, ctx):
        if self.queue:
            url, title = self.queue.pop(0)
            self.current_song = title  # Update current track here
            source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
            ctx.voice_client.play(source, after=lambda _: self.client.loop.create_task(self.play_next(ctx)))
            await ctx.send(f'## **Now Playing **🎵 \n > **{title}**')

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            await ctx.send("## **Current track has been skipped **⏩")
            ctx.voice_client.stop()

    @commands.command()
    async def queue(self, ctx):
        if not self.queue:
            await ctx.send("**NeroBot's queue is currently empty **🪹")
        else:
            # Format currently playing track and queue list separately
            queueString = f"## **Currently Playing** 🎵\n> **{self.current_song}**\n\n## **Up Next** ↩️\n"
            queueString += "\n".join([f"{index + 1}. {title}" for index, (_, title) in enumerate(self.queue)])
            await ctx.send(queueString)

    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("**NeroBot has disconnected from the voice channel **😘")

    @commands.command()
    async def clear(self, ctx):
        self.queue.clear()
        await ctx.send("## **The track queue has been cleared **🗑️")

    @commands.command()
    async def commands(self, ctx):
        commandlist = """ 
        ## __**NeroBot Commands**__📋\n- **!play <title>** - play a track from youtube\n- **!skip** - skip the current track\n- **!queue** - view the current track queue \n- **!clear** - clears the queue of all tracks\n- **!leave** - disconnects NeroBot\n- **!commands** -  display all relevant commands'
        """
        await ctx.send(commandlist)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

client = commands.Bot(command_prefix="!", intents=intents)

async def main():
    await client.add_cog(MusicBot(client))
    await client.start(api_token)

asyncio.run(main())
