import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from src.services.ai_service import analyze_text

_RATING_CONFIG = {
    "green": {
        "color": discord.Color.green(),
        "title": "✅ No Issues Detected",
    },
    "yellow": {
        "color": discord.Color.yellow(),
        "title": "⚠️ Monitor — Potential Concern",
    },
    "red": {
        "color": discord.Color.red(),
        "title": "🚨 Action Needed",
    },
}

_DEFAULT_CONFIG = {
    "color": discord.Color.greyple(),
    "title": "🔍 Analysis Complete",
}


class AuditCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="audit", description="Analyze text for compliance risks")
    @app_commands.describe(text="The text to analyze for policy violations or risks")
    async def audit(self, interaction: discord.Interaction, text: str) -> None:
        await interaction.response.defer(ephemeral=True)

        result = await asyncio.to_thread(analyze_text, text)

        rating = result.get("rating", "unknown")
        summary = result.get("summary", "No summary returned.")

        cfg = _RATING_CONFIG.get(rating, _DEFAULT_CONFIG)

        embed = discord.Embed(
            title=cfg["title"],
            description=summary,
            color=cfg["color"],
        )
        embed.set_footer(text="Analyzed by Gemini | /audit")

        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AuditCog(bot))
