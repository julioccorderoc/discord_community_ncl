import asyncio
import discord
from discord.ext import commands

import src.config as config
from src.models.schemas import ActivityType
from src.services.activity_service import log_activity, upsert_user


class ActivityCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        # Redirect DMs to the community manager instead of leaving them unanswered.
        if message.guild is None:
            if config.COMMUNITY_MANAGER_ID is not None:
                try:
                    manager = await self.bot.fetch_user(config.COMMUNITY_MANAGER_ID)
                    await message.author.send(
                        f"Hey! I'm a bot and can't reply to DMs. "
                        f"Reach out to **{manager.display_name}** directly:\n"
                        f"https://discord.com/users/{manager.id}"
                    )
                except discord.HTTPException:
                    await message.author.send(
                        "Hey! I'm a bot and can't reply to DMs. "
                        "Please reach out to a community manager in the NCL server."
                    )
            return

        author = message.author
        await asyncio.to_thread(
            upsert_user,
            author.id,
            str(author),
            str(author.display_avatar.url) if author.display_avatar else None,
            getattr(author, "joined_at", None),
        )
        await asyncio.to_thread(
            log_activity,
            author.id,
            ActivityType.MESSAGE_SENT,
            message.channel.id,
            {"message_id": message.id},
        )

    @commands.Cog.listener()
    async def on_reaction_add(
        self, reaction: discord.Reaction, user: discord.User | discord.Member
    ) -> None:
        if user.bot:
            return
        await asyncio.to_thread(
            upsert_user,
            user.id,
            str(user),
            str(user.display_avatar.url) if user.display_avatar else None,
            getattr(user, "joined_at", None),
        )
        await asyncio.to_thread(
            log_activity,
            user.id,
            ActivityType.REACTION_ADD,
            reaction.message.channel.id,
            {"message_id": reaction.message.id, "emoji": str(reaction.emoji)},
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ActivityCog(bot))
