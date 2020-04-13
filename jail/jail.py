"""discord red-bot jail"""
from redbot.core import commands, Config


class JailCog(commands.Cog):
    """Jail Cog"""

    def __init__(self, bot):
        self.bot = bot
        self.settings = Config.get_conf(self, identifier=1249812384)
