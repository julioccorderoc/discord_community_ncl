import asyncio
import discord
from discord import app_commands
from discord.ext import commands

import src.config as config
from src.models.schemas import TicketStatus
from src.services.activity_service import upsert_user
from src.services.ticket_service import (
    create_ticket,
    get_ticket_by_channel,
    log_ticket_event,
    resolve_ticket,
)


class TicketModal(discord.ui.Modal, title="Open a Support Ticket"):
    """Modal that pops up when a user clicks the Open Ticket button."""

    subject = discord.ui.TextInput(
        label="What do you need help with?",
        placeholder="Briefly describe your issue...",
        min_length=5,
        max_length=255,
        style=discord.TextStyle.short,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        # Defer immediately — the I/O chain can take several seconds.
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        user = interaction.user
        subject_text = self.subject.value

        if config.STAFF_ROLE_ID is None:
            await interaction.followup.send(
                "Ticket system is not configured. Please contact an administrator.",
                ephemeral=True,
            )
            return

        staff_role = guild.get_role(config.STAFF_ROLE_ID)
        if staff_role is None:
            await interaction.followup.send(
                "Staff role not found. Please contact an administrator.",
                ephemeral=True,
            )
            return

        # Ensure user row exists before inserting ticket (FK constraint).
        await asyncio.to_thread(
            upsert_user,
            user.id,
            str(user),
            str(user.display_avatar.url) if user.display_avatar else None,
            getattr(user, "joined_at", None),
        )

        # Build channel permission overwrites.
        category = None
        if config.TICKET_CATEGORY_ID is not None:
            category = guild.get_channel(config.TICKET_CATEGORY_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
            ),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
            ),
            staff_role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
            ),
        }

        channel_name = f"ticket-{user.name.lower().replace(' ', '-')}"
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            reason=f"Support ticket by {user} — {subject_text}",
        )

        ticket = await asyncio.to_thread(
            create_ticket,
            user.id,
            subject_text,
            ticket_channel.id,
        )

        await asyncio.to_thread(
            log_ticket_event,
            ticket.id,
            user.id,
            f"Ticket opened by {user} (ID: {user.id}). Subject: {subject_text}",
        )

        embed = discord.Embed(
            title=f"Ticket #{ticket.id} — {subject_text}",
            description=(
                f"Hello {user.mention}, a staff member will be with you shortly.\n\n"
                f"**Subject:** {subject_text}\n"
                f"**Status:** {TicketStatus.OPEN.value.capitalize()}\n\n"
                f"When resolved, staff will run `!close` to close this ticket."
            ),
            color=discord.Color.green(),
        )
        embed.set_footer(text=f"Opened by {user} | ID: {user.id}")
        await ticket_channel.send(
            content=f"{user.mention} {staff_role.mention}",
            embed=embed,
        )

        await interaction.followup.send(
            f"Your ticket has been opened! Head to {ticket_channel.mention}",
            ephemeral=True,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        print(f"[TicketModal] Error: {error!r}")
        try:
            await interaction.followup.send(
                "Something went wrong while opening your ticket. Please try again.",
                ephemeral=True,
            )
        except discord.HTTPException:
            pass


class TicketView(discord.ui.View):
    """Persistent view containing the Open Ticket button."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Open Ticket",
        style=discord.ButtonStyle.primary,
        emoji="🎫",
        custom_id="ticket_system:open_ticket",
    )
    async def open_ticket_button(
        self, interaction: discord.Interaction, _button: discord.ui.Button
    ) -> None:
        await interaction.response.send_modal(TicketModal())


class TicketsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Re-register the persistent view on every startup so old buttons still work.
        self.bot.add_view(TicketView())

    @commands.command(name="setup-tickets")
    @commands.has_permissions(administrator=True)
    async def setup_tickets(self, ctx: commands.Context) -> None:
        """Post the persistent Open Ticket button in the current channel. (Admin only)"""
        embed = discord.Embed(
            title="NCL Support",
            description=(
                "Need help? Click the button below to open a private support ticket.\n"
                "A staff member will respond as soon as possible."
            ),
            color=discord.Color.blurple(),
        )
        await ctx.send(embed=embed, view=TicketView())
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

    @app_commands.command(name="help", description="Open a support ticket")
    @app_commands.describe(subject="Briefly describe your issue")
    async def help_command(
        self, interaction: discord.Interaction, subject: str
    ) -> None:
        """Open a support ticket directly via slash command."""
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        user = interaction.user

        if config.STAFF_ROLE_ID is None:
            await interaction.followup.send(
                "Ticket system is not configured. Please contact an administrator.",
                ephemeral=True,
            )
            return

        staff_role = guild.get_role(config.STAFF_ROLE_ID)
        if staff_role is None:
            await interaction.followup.send(
                "Staff role not found. Please contact an administrator.",
                ephemeral=True,
            )
            return

        await asyncio.to_thread(
            upsert_user,
            user.id,
            str(user),
            str(user.display_avatar.url) if user.display_avatar else None,
            getattr(user, "joined_at", None),
        )

        category = None
        if config.TICKET_CATEGORY_ID is not None:
            category = guild.get_channel(config.TICKET_CATEGORY_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
            ),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
            ),
            staff_role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
            ),
        }

        channel_name = f"ticket-{user.name.lower().replace(' ', '-')}"
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            reason=f"Support ticket by {user} — {subject}",
        )

        ticket = await asyncio.to_thread(
            create_ticket,
            user.id,
            subject,
            ticket_channel.id,
        )

        await asyncio.to_thread(
            log_ticket_event,
            ticket.id,
            user.id,
            f"Ticket opened by {user} (ID: {user.id}). Subject: {subject}",
        )

        embed = discord.Embed(
            title=f"Ticket #{ticket.id} — {subject}",
            description=(
                f"Hello {user.mention}, a staff member will be with you shortly.\n\n"
                f"**Subject:** {subject}\n"
                f"**Status:** {TicketStatus.OPEN.value.capitalize()}\n\n"
                f"When resolved, staff will run `!close` to close this ticket."
            ),
            color=discord.Color.green(),
        )
        embed.set_footer(text=f"Opened by {user} | ID: {user.id}")
        await ticket_channel.send(
            content=f"{user.mention} {staff_role.mention}",
            embed=embed,
        )

        await interaction.followup.send(
            f"Your ticket has been opened! Head to {ticket_channel.mention}",
            ephemeral=True,
        )

    @commands.command(name="close")
    async def close_ticket(self, ctx: commands.Context) -> None:
        """Close the current ticket channel. Must be run inside a ticket channel."""
        channel = ctx.channel

        ticket = await asyncio.to_thread(get_ticket_by_channel, channel.id)
        if ticket is None:
            await ctx.send(
                "This command can only be used inside a ticket channel.",
                delete_after=5.0,
            )
            return

        if ticket.status in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
            await ctx.send("This ticket is already closed.", delete_after=5.0)
            return

        resolved_ticket = await asyncio.to_thread(resolve_ticket, channel.id)
        if resolved_ticket is None:
            await ctx.send(
                "Failed to resolve ticket in database. Please try again.",
                delete_after=5.0,
            )
            return

        await asyncio.to_thread(
            log_ticket_event,
            resolved_ticket.id,
            ctx.author.id,
            f"Ticket closed by {ctx.author} (ID: {ctx.author.id}). Status set to RESOLVED.",
        )

        await ctx.send(
            f"Ticket #{resolved_ticket.id} resolved by {ctx.author.mention}. "
            "This channel will be deleted in 5 seconds."
        )
        await asyncio.sleep(5)

        try:
            await channel.delete(
                reason=f"Ticket #{resolved_ticket.id} resolved by {ctx.author}"
            )
        except discord.NotFound:
            pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TicketsCog(bot))
