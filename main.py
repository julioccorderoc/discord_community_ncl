import asyncio
import discord
from discord.ext import commands
from src.config import DISCORD_BOT_TOKEN

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready() -> None:
    synced = await bot.tree.sync()
    print(f"Bot ready: {bot.user} (ID: {bot.user.id}) | Synced {len(synced)} slash command(s)")


@bot.command(name="ping")
async def ping(ctx: commands.Context) -> None:
    await ctx.send("Pong!")


async def main() -> None:
    async with bot:
        await bot.load_extension("src.cogs.activity")
        await bot.load_extension("src.cogs.tickets")
        await bot.load_extension("src.cogs.audit")
        await bot.start(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
