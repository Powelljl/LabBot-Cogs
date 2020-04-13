"""discord red-bot jail"""
from redbot.core import commands, Config, checks
import discord


class JailCog(commands.Cog):
    """Jail Cog"""

    def __init__(self, bot):
        self.bot = bot
        self.settings = Config.get_conf(self, identifier=1249812384)

    @commands.command(name="jail")
    @commands.guild_only()
    @checks.mod()
    async def jail(
        self,
        ctx: commands.Context,
        user: discord.Member,
        *,
        time: int = None
    ):
        pass

    @commands.command(name="bail")
    @commands.guild_only()
    @checks.mod()
    async def bail(
        self,
        ctx: commands.Context,
        user: discord.Member
    ):
        pass
