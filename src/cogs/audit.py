import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands

import src.config as config
from src.services.ai_service import analyze_text, log_ai_audit

log = logging.getLogger(__name__)

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

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(analyze_text, text),
                timeout=config.GEMINI_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            log.warning("[audit] Gemini timed out after %ds", config.GEMINI_TIMEOUT_SECONDS)
            await interaction.followup.send(
                "The analysis timed out. Please try again or contact an admin.",
                ephemeral=True,
            )
            return
        except Exception as exc:
            log.error("[audit] Gemini call failed: %r", exc)
            await interaction.followup.send(
                "The analysis failed due to an unexpected error. Please contact an admin.",
                ephemeral=True,
            )
            return

        rating = result.get("rating", "unknown")
        summary = result.get("summary", "No summary returned.")

        cfg = _RATING_CONFIG.get(rating, _DEFAULT_CONFIG)

        embed = discord.Embed(
            title=cfg["title"],
            description=summary,
            color=cfg["color"],
        )
        embed.set_footer(text=f"Analyzed by {config.GEMINI_MODEL} | /audit")

        await interaction.followup.send(embed=embed, ephemeral=True)

        # Fire-and-forget DB write — never blocks the Discord response.
        asyncio.create_task(
            asyncio.to_thread(
                log_ai_audit,
                interaction.user.id,
                "/audit",
                text,
                result.get("raw_response"),
                result.get("tokens_used"),
                result.get("elapsed_ms"),
            )
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AuditCog(bot))
