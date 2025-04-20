import asyncio
import random
import time
import discord
import yt_dlp

from playlist_generator import generate_songs
from colorama import Fore, init
from discord.ext import commands

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}
YDL_OPTIONS = {
    'format': 'bestaudio',
    'noplaylist': True,
    'quiet': True
}
YDL_PLAYLIST_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': False,
    'quiet': True,
    'ignoreerrors': True,  # Skip unavailable videos
}

init(autoreset=True)
systemColor = Fore.LIGHTBLUE_EX
userInputColor = Fore.LIGHTGREEN_EX
statusColor = Fore.CYAN
userColor = Fore.LIGHTMAGENTA_EX
addedToQueue = Fore.LIGHTYELLOW_EX

class MusicBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.track_queue = []
        self.last_now_playing_msg_id = None
        self.active_track = None
        self.paused = False
        self.looping = False
        self.looped_song = None

    async def player_loop(self, ctx):
        # Constantly check for items in the track queue
        while True:
            if self.track_queue and ctx.voice_client and not ctx.voice_client.is_playing() and not self.paused:
                if self.looping:
                    title, url = self.active_track

                    self.play_through_voice_client(ctx, url)
                else:
                    # Remove the FIFO item and store it as a local variable
                    url, title = self.track_queue.pop(0)
                    self.active_track = title, url

                    self.play_through_voice_client(ctx, url)

                    await self.update_previous_now_playing_message(ctx, title)

            if not self.track_queue and not ctx.voice_client.is_playing():
                self.active_track = None

            await asyncio.sleep(1)

    def play_through_voice_client(self, ctx, url):
        # Generate a ffmpeg source from the url and play it in the voice channel
        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
        ctx.voice_client.play(source,after=lambda _: asyncio.run_coroutine_threadsafe(self.player_loop(ctx), self.client.loop))
        print(f"{systemColor}[System] - [{time.ctime()}] - Now playing: {self.active_track[0]}")

    async def update_previous_now_playing_message(self, ctx, title):
        # If there is a previous "now playing" message
        if self.last_now_playing_msg_id:
            # Delete it
            try:
                last_msg = await ctx.channel.fetch_message(self.last_now_playing_msg_id)
                await last_msg.delete()
            except discord.NotFound:
                pass
        # Set the class attribute as the new one and send an updated "now-playing" message
        new_msg = await ctx.send(f'## **Now Playing **🎵 \n > **{title}**')
        self.last_now_playing_msg_id = new_msg.id

    async def find_song_and_add_to_queue(self, ctx, description, generated):
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{description}", download=False)
            if 'entries' in info:
                info = info['entries'][0]
            url = info['url']
            title = info['title']
            self.track_queue.append((url, title))
            print(
                f"{userInputColor}[User] - [{time.ctime()}] - {addedToQueue}{ctx.author.display_name} added {title} to queue")
        if ctx.voice_client.is_playing() and not generated:
            await ctx.send(f'## **Added to Queue **✅ \n> **{title}**')

    @commands.command()
    async def connect(self, ctx):
        self.paused = False
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        try:
            if not voice_channel:  # User summoned the bot but wasn't in a channel
                print(
                    f'{Fore.LIGHTBLUE_EX}[System] - [{time.ctime()}] - {ctx.author.display_name} tried to summon NeroBot via play command but was not in a voice channel')
                return await ctx.send("## **You're not in a voice channel **❌")

            if not ctx.voice_client:  # Bot is not in a voice channel
                print(
                    f'{systemColor}[System] - [{time.ctime()}] - NeroBot joined "{voice_channel.name}" voice channel via play command')
                return await voice_channel.connect()

            elif ctx.voice_client.channel != voice_channel:  # Bot is in a different voice channel
                print(
                    f'{systemColor}[System] - [{time.ctime()}] - NeroBot moved to "{voice_channel.name}" voice channel')
                return await ctx.voice_client.move_to(voice_channel)
        except Exception as e:
            print(f'{systemColor}[System] - [{time.ctime()}] - {e}')

    @commands.command()
    async def play(self, ctx, *, search):
        await self.connect(ctx)  # Ensure the bot connects to the user's voice channel

        async with ctx.typing():
            await self.find_song_and_add_to_queue(ctx, search, False)

        if not ctx.voice_client.is_playing():
            await self.player_loop(ctx)

    @commands.command()
    async def p(self, ctx, *, search):
        await self.play(ctx, search=search)

    @commands.command()
    async def playlist(self, ctx, *, search):
        playlist_shuffler = []

        await self.connect(ctx)  # Ensure the bot connects to the user's voice channel

        async with ctx.typing():
            try:
                with yt_dlp.YoutubeDL(YDL_PLAYLIST_OPTIONS) as ydl:
                    playlist_info = ydl.extract_info(search, download=False)
                    print(f"{userInputColor}[User] - [{time.ctime()}] - {addedToQueue}{ctx.author.display_name} added entries in '{playlist_info['title']}' to queue.")

                    # Add all the songs in the extracted playlist to a temp shuffler playlist
                    for entry in playlist_info.get('entries', []):
                        if not entry:  # Skip invalid or unavailable videos
                            continue
                        try:
                            url = entry['url']
                            title = entry['title']
                            if url and title:
                                playlist_shuffler.append((url, title))
                        except Exception as e:
                            print(f"{systemColor}[System] - [{time.ctime()}] - Error adding song: {e}")
                            continue

                    # Pop a random item from the temp playlist to the queue
                    while playlist_shuffler:
                        url, title = playlist_shuffler.pop(random.randrange(len(playlist_shuffler)))
                        self.track_queue.append((url, title))
                        print(f"{userInputColor}[User] - [{time.ctime()}] - {userColor}{ctx.author.display_name} added {title} to queue")

                    await ctx.send(f"## **Added Playlist Entries to Queue **✅ \n> **{playlist_info['title']} **")
            except Exception as e:
                print(f"{systemColor}[System] - [{time.ctime()}] - Error extracting playlist: {e}")
                await ctx.send(f"Error extracting playlist, ensure playlist is public and contains valid entries.")

        if not ctx.voice_client.is_playing():
            await self.player_loop(ctx)

    @commands.command()
    async def generate(self, ctx, description: str = "random", count: int = 5):
        # limit maximum songs to 20
        if count >= 20:
            await ctx.send("## Number of songs requested must be less than 20. ")
            return

        # connect the bot and initialize the queue string
        await self.connect(ctx)
        queue_string = "## Generated the following songs and added it to queue ✅:\n"

        # generate the song list and find and add each song to the queue as well as the queue list string
        async with ctx.typing():
            song_list = generate_songs(description, count)
            for song in song_list:
                queue_string += f"- {song}\n"
                await self.find_song_and_add_to_queue(ctx, song, True)

        # send the queue string
        await ctx.send(queue_string)

        # start the player loop if not playing
        if not ctx.voice_client.is_playing():
            await self.player_loop(ctx)

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            await ctx.send(f"## **Current track ({self.active_track[0]}) has been skipped **⏩")
            self.active_track = None
            ctx.voice_client.stop()
            print(f'{userInputColor}[User] - [{time.ctime()}] - {userColor}{ctx.author.display_name} skipped {self.active_track}')

    @commands.command()
    async def s(self, ctx):
        await self.skip(ctx)

    @commands.command()
    async def pause(self, ctx):
        if not self.paused:
            self.paused = True
            self.track_queue.insert(0, (self.active_track[1], self.active_track[0]))
            ctx.voice_client.stop()
            self.active_track = None
            await ctx.send(f"## **Queue Paused** 🎵")
            print(f'{userInputColor}[User] - [{time.ctime()}] - {userColor}{ctx.author.display_name} paused the queue')
        else:
            await ctx.send(f"## **Queue is already paused** 🎵")

    @commands.command()
    async def resume(self, ctx):
        if self.paused:
            self.paused = False
            await ctx.send(f"## **Queue Resumed** 🎵")
            print(f'{userInputColor}[User] - [{time.ctime()}] - {userColor}{ctx.author.display_name} resumed the queue')
        else:
            await ctx.send(f"## **Queue already playing** 🎵")

    @commands.command()
    async def loop(self, ctx):
        if not self.is_playing():
            await ctx.send(f"There is no active song to loop")
        elif self.looping:
            await ctx.send(f"Already looping!")
        else:
            self.looped_song = self.active_track[0]
            self.looping = True
            print(f'{userInputColor}[User] - [{time.ctime()}] - {userColor}{ctx.author.display_name} looped the current song {self.looped_song}')
            await ctx.send(f"## Looping {self.active_track[0]} until !unloop")
        return

    @commands.command()
    async def diagnostics(self, ctx):
        await ctx.send(f""" ## NeroBot Instance Diagnostics
        ### Time : {time.ctime()} 
        self.client = {self.client}
        self.track_queue = {self.track_queue}
        self.last_now_playing_msg_id = {self.last_now_playing_msg_id}
        self.active_track = {self.active_track}
        self.paused = {self.paused}
        self.looping = {self.looping}
        self.looped_song = {self.looped_song}
        """)
        return

    @commands.command()
    async def unloop(self, ctx):
        if not self.is_playing():
            await ctx.send(f"There is no active song to unloop")
        elif not self.looping:
            await ctx.send(f"Already not looping current track!")
        else:
            print(f'{userInputColor}[User] - [{time.ctime()}] - {userColor}{ctx.author.display_name} unlooped the current song')
            self.looped_song = None
            self.looping = False
            self.track_queue.pop(0)
            await ctx.send(f"## Unlooping!")
        return

    @commands.command()
    async def queue(self, ctx):
        # If the queue is empty and there is no active track
        if self.active_track or self.track_queue:
            queueString = f"## **Currently Playing** 🎵\n> {self.active_track[0]} \n## **Up Next** ↩️\n"
            if self.track_queue:
                queueString += "\n".join([f"{index + 1}. {title}" for index, (_, title) in enumerate(self.track_queue)])
            else:
                queueString += "No upcoming tracks."
            await ctx.send(queueString)
            print(
                f'{userInputColor}[User] - [{time.ctime()}] - {userColor}{ctx.author.display_name} requested the track queue')
        else:
            await ctx.send("## **NeroBot's queue is currently empty**🪹")
            print(
                f'{userInputColor}[User] - [{time.ctime()}] - {userColor}{ctx.author.display_name} requested the track queue but it was empty')

    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            print(f'{userInputColor}[User] - [{time.ctime()}] - {userColor}{ctx.author.display_name} disconnected NeroBot from "{ctx.voice_client.channel.name}"')
            await ctx.send("## **NeroBot has disconnected from the voice channel **👋")

    @commands.command()
    async def clear(self, ctx):
        self.track_queue.clear()
        await ctx.send("## **The track queue has been cleared **🗑️")
        print(f'{userInputColor}[User] - [{time.ctime()}] - {userColor}{ctx.author.display_name} displayed the current track queue')

    @commands.command()
    async def goodbot(self, ctx):
        await ctx.send(f'## **Thanks {ctx.author.display_name} ** 🥰')
        print(f'{userInputColor}[User] - [{time.ctime()}] - {userColor}{ctx.author.display_name} thanked NeroBot')

    @commands.command()
    async def about(self, ctx):
        await ctx.send("# About NeroBot :robot:\n- NeroBot is a youtube-based discord music bot written in Python. \n - It uses the following libraries: yt_dlp, discord.py, dotenv, openai, ffmpeg, and other internal libraries.\n- You can access the git repository and view the development timeline [here](https://github.com/JorenDryden/nerobot). \n© 2025 Joren Dryden. All Rights Reserved.")
        print(f'{userInputColor}[User] - [{time.ctime()}] - {userColor}{ctx.author.display_name} displayed about me')

    @commands.command()
    async def moo(self, ctx):
        message = "https://giphy.com/gifs/leagueoflegends-3oKIP73vEZmJjFNXtC"
        await ctx.send(message)
        print(f'{userInputColor}[User] - [{time.ctime()}] - {userColor}{ctx.author.display_name} displayed the secret')

    @commands.command()
    async def support(self, ctx):
        command_list = """## __**NeroBot Commands**__ 📋\n- **!play <title>** - play a track from youtube\n- **!skip** - skip the current track\n -**!pause** - pause the queue \n- **!resume** - resume the queue \n- **!queue** - view the current track queue \n- **!clear** - clears the queue of all tracks\n- **!leave** - disconnects NeroBot\n- **!support** -  display all relevant commands\n- **!goodbot** - thank the bot for its service\n- **!about** - about NeroBot"""
        await ctx.send(command_list)
        print(f'{userInputColor}[User] - [{time.ctime()}] - {userColor}{ctx.author.display_name} displayed the command list')

    @commands.command()
    async def update(self, ctx):
        message = ("""#  **:loudspeaker: NeroBot Update - (v1.1) :loudspeaker:**
        ## Hello! I've been updated to support more functionality!  
        
        ### :rocket: What's New:  
        :small_blue_diamond: `!pause` - Pause the queue  
        :small_blue_diamond: `!resume` - Resume listening to the queue
        :small_blue_diamond: :tools: Bug fixes and improvements
        
        ### Enjoy the update! :musical_note::robot:""")

        for channel in ctx.guild.text_channels:
            if ctx.author.guild_permissions.administrator:
                if channel.permissions_for(ctx.guild.me).send_messages:
                    await channel.send(message)
            else:
                await channel.send("You do not have permission to do that.")
            break

    def is_paused(self):
        return self.paused

    def is_playing(self):
        return bool(self.track_queue or self.active_track)