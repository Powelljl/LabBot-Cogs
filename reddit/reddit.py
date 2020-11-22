"""discord red-bot reddit feed"""
import discord
from redbot.core import checks, tasks, commands, Config
import aiohttp
from datetime import datetime as dt

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'}
reddit_colour = 0xFF4500

class Submission:
    def __init__(self, submission):
        self.title = submission['title']
        self.text = submission['selftext']
        self.author = submission['author']
        self.subreddit = submission['subreddit']
        self.timestamp = dt.fromtimestamp(submission['data']['created_utc'])
        self.id = submission['id']
        self.preview = submission['preview']['images'][0]['source']['url'] if 'preview' in submission else None
        self.embed = self.make_embed

    def make_embed(self):
        embed = discord.Embed(title=self.title, colour=reddit_colour, description=self.text, timestamp=self.timestamp)
        embed.set_thumbnail(url=self.preview)
        return embed

class Subreddit:
    def __init__(self, name):
        self.name = name

    async def new(self):
        url = f'https://reddit.com/r/{self.name}/new.json'
        async with aiohttp.ClientSession() as session:
            try:
                with async_timeout.timeout(10):
                    async with session.get(url) as response:
                        data = await response.json()
                        return [Submission(i['data']) for i in data['data']['children']]
            except Exception as e:
                print(data)
                print(e)
        if not data['data']['children']:
            raise NoListingsFound
        return [Submission(i) for i in data['data']['children']]

    async def hot(self):
        url = f'https://reddit.com/r/{self.name}/new.json'
        async with aiohttp.ClientSession() as session:
            try:
                with async_timeout.timeout(10):
                    async with session.get(url) as response:
                        data = await response.json()
                        return [Submission(i['data']) for i in data['data']['children']]
            except Exception as e:
                print(data)
                print(e)
        if not data['data']['children']:
            raise NoListingsFound
        return [Submission(i) for i in r['data']['children']]

class RedditCog(commands.Cog):
    """Reddit Feed cog"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=377212919068229633004)

        default_guild_config = {
            "feeds": [], # Regular feeds - [{'subreddit': str, 'channel_id': int}]
            "filtered_feeds": [] # Feeds filtered by post flair - [{'subreddit': str, 'channel_id': int, 'filter': {'flair': str, 'title': str}}]
        }

        self.config.register_guild(**default_guild_config)

# Events

    @commands.Cog.listener()
    async def on_ready():
        self.scan_subreddits.start()

    @commands.Cog.listener()
    async def on_disconnect(self):
        self.scan_subreddits.cancel()

# Command groups

    @checks.admin()
    @commands.group(name='reddit', pass_context=True)
    async def _feed(self, ctx):
        """Subscribe/Unsubscribe to Reddit feeds"""
        pass

# Commands

    @_feed.command(name='subscribe')
    async def subscribe(self, ctx, subreddit, channel: discord.TextChannel):
        """Subscribe to a Reddit feed
        
        Example:
        - `[p]redditfeed subscribe <subreddit> <channel>`
        """
        async with self.config.guild(ctx.guild).feeds() as feeds:
            if {'subreddit': subreddit.lower(), 'channel_id': channel.id} in feeds:
                error_embed = await self.make_error_embed(ctx, error_type='FeedExists') 
                await ctx.send(embed=error_embed)
                return
            feeds.append({'subreddit': subreddit.lower(), 'channel_id': channel.id})
            success_embed = discord.Embed(title='Subscribed to feed', description=f"<#{channel.id}> **-** r/{subreddit.lower()}", colour=ctx.guild.me.colour)
            await ctx.send(embed=success_embed)

    @_feed.command(name='unsubscribe')
    async def unsubscribe(self, ctx, subreddit: str, channel: discord.TextChannel):
        """Unsubscribe from a Reddit feed
        
        Example:
        - `[p]redditfeed unsubscribe <subreddit>`
        """
        async with self.config.guild(ctx.guild).feeds() as feeds:
            if {'subreddit': subreddit.lower(), 'channel_id': channel.id} not in feeds:
                error_embed = self.make_error_embed(ctx, error_type='FeedNotFound')
                await ctx.send(embed=error_embed)
                return

            feeds.remove({'subreddit': subreddit.lower(), 'channel_id': channel.id})
            success_embed = discord.Embed(title='Unsubscribed from feed', description=f"<#{channel.id}> **-** r/{subreddit.lower()}", colour=ctx.guild.me.colour)
            await ctx.send(embed=success_embed)

# Tasks

    @tasks.loop(seconds=30)
    async def check_subreddits(self):
        all_guild_config = await self.config.all_guilds()
        seen_posts = await self.config['seen_posts']
        subreddits = {x for y in [all_guild_config[i]['feeds'] for i in all_guild_config.keys()] for x in y}

        for subreddit in subreddits:
            sub = Subreddit(subreddit)
            posts = sub.new()

            if not [i for i in posts if i.id not in seen_posts]:
                continue

            for guild in all_guild_config:
                for i in [i for i in all_guild_config[guild]['feeds'] if i['subreddit'] == sub.name]:
                    guild_object = await discord.fetch_guild(guild)
                    channel = await guild_object.fetch_channel(i['channel_id'])
                    for post in posts:
                        await channel.send(embed=post.embed)

                for i in [i for i in all_guild_config[guild]['feeds'] if i['subreddit'] == sub.name]:
                    guild_object = await discord.fetch_guild(guild)
                    channel = await guild_object.fetch_channel(i['channel_id'])
                    for post in posts:
                        if (i['filter']['title'] in post.title.lower()) and (i['filter']['flair'] == True):
                            await channel.send(embed=post.embed)

# Helper functions

    async def make_error_embed(self, ctx, error_type: str = ''):
        error_msgs = {
            'FeedExists': 'That channel is already subscribed to that subreddit',
            'FeedNotFound': 'There is no active feed for that subreddit'
        }
        return discord.Embed(title='Error', description=error_msgs[error_type], colour=ctx.guild.me.colour)

