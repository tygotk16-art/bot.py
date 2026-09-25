import os
import discord
from discord.ext import commands

TOKEN = os.getenv("MTU1MzA3NjAwMjI5OTcxNTY3NA.GMq25D.1k7z69ilROU77umDyV6XgVu-EsHxrFjS5VbkY8")

STAFF_ROLES = ["🛠 Admin", "🔨 Moderator"]
LOG_CHANNEL_NAME = "📜-ticket-logs"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

TICKET_TYPES = {
    "support": "🎫 General Support",
    "orders": "💰 Order Help",
    "reports": "⚠️ Report User",
    "middleman": "🤝 Middleman Request",
    "applications": "📝 Application",
    "other": "❓ Other",
}

class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        guild = interaction.guild

        log_channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
        if log_channel:
            await log_channel.send(f"🔒 Ticket closed: {channel.name} by {interaction.user.mention}")

        await interaction.response.send_message("Closing ticket...", ephemeral=True)
        await channel.delete()

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def create_ticket(self, interaction: discord.Interaction, ticket_key: str):
        guild = interaction.guild
        user = interaction.user

        category = discord.utils.get(guild.categories, name="🎫 Tickets")
        if category is None:
            category = await guild.create_category("🎫 Tickets")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
            ),
        }

        for role_name in STAFF_ROLES:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    manage_messages=True,
                )

        channel_name = f"{ticket_key}-{user.name}".lower().replace(" ", "-")
        ticket_channel = await guild.create_text_channel(
            channel_name,
            category=category,
            overwrites=overwrites,
        )

        embed = discord.Embed(
            title=TICKET_TYPES[ticket_key],
            description=f"{user.mention}, describe your issue and staff will assist you.",
        )

        await ticket_channel.send(embed=embed, view=CloseView())
        await interaction.response.send_message(
            f"Ticket created: {ticket_channel.mention}",
            ephemeral=True,
        )

    @discord.ui.button(label="General Support", style=discord.ButtonStyle.primary)
    async def support(self, interaction, button):
        await self.create_ticket(interaction, "support")

    @discord.ui.button(label="Order Help", style=discord.ButtonStyle.success)
    async def orders(self, interaction, button):
        await self.create_ticket(interaction, "orders")

    @discord.ui.button(label="Report User", style=discord.ButtonStyle.danger)
    async def reports(self, interaction, button):
        await self.create_ticket(interaction, "reports")

    @discord.ui.button(label="Middleman", style=discord.ButtonStyle.secondary)
    async def middleman(self, interaction, button):
        await self.create_ticket(interaction, "middleman")

    @discord.ui.button(label="Application", style=discord.ButtonStyle.primary, row=1)
    async def applications(self, interaction, button):
        await self.create_ticket(interaction, "applications")

    @discord.ui.button(label="Other", style=discord.ButtonStyle.secondary, row=1)
    async def other(self, interaction, button):
        await self.create_ticket(interaction, "other")

@bot.event
async def on_ready():
    bot.add_view(TicketView())
    bot.add_view(CloseView())
    print(f"Logged in as {bot.user}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    guild = ctx.guild

    category = discord.utils.get(guild.categories, name="🎫 Tickets")
    if category is None:
        category = await guild.create_category("🎫 Tickets")

    logs = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
    if logs is None:
        await guild.create_text_channel(LOG_CHANNEL_NAME)

    panel = discord.utils.get(guild.text_channels, name="ticket-panel")
    if panel is None:
        panel = await guild.create_text_channel("ticket-panel", category=category)

    embed = discord.Embed(
        title="Ticket System",
        description="Choose a ticket type below."
    )

    await panel.send(embed=embed, view=TicketView())
    await ctx.send("✅ Ticket system created.")

bot.run(TOKEN)
