import asyncio
import discord
from discord.ext import commands

import src.config as config
from src.services.activity_service import upsert_user
from src.services.presence_service import (
    close_all_open_sessions,
    close_presence_session,
    open_presence_session,
)


class PresenceCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        """Close any stale open sessions left over from a previous bot run."""
        await asyncio.to_thread(close_all_open_sessions)

    @commands.Cog.listener()
    async def on_presence_update(
        self, before: discord.Member, after: discord.Member
    ) -> None:
        if after.bot or after.id in config.IGNORED_USER_IDS:
            return

        before_status = str(before.status)
        after_status = str(after.status)

        if after_status == "offline":
            # Member went offline — close their open session.
            await asyncio.to_thread(close_presence_session, after.id)

        elif before_status == "offline":
            # Member came online — ensure they exist in discord_users, then open a session.
            await asyncio.to_thread(
                upsert_user,
                after.id,
                str(after),
                str(after.display_avatar.url) if after.display_avatar else None,
                getattr(after, "joined_at", None),
            )
            await asyncio.to_thread(open_presence_session, after.id, after_status)

        elif before_status != after_status:
            # Status changed between online/idle/dnd — close old session, open new one.
            await asyncio.to_thread(close_presence_session, after.id)
            await asyncio.to_thread(open_presence_session, after.id, after_status)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PresenceCog(bot))
