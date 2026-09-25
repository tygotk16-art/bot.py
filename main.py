import os
import asyncio
import discord
from discord.ext import commands

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1552705732481126480
STAFF_ROLE_NAME = "Staff"

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN environment variable is not set.")

# =========================
# INTENTS
# =========================

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True

# =========================
# CHANNEL STRUCTURE
# =========================

CHANNEL_STRUCTURE = {
    "Information": [
        "rules",
        "announcements"
    ],
    "Marketplace": [
        "buying",
        "selling",
        "vouches",
        "middleman-requests"
    ],
    "Support": [
        "tickets",
        "reports"
    ],
    "Staff": [
        "staff-chat",
        "logs",
        "📜-ticket-logs"
    ],
    "DONUT SMP": [
        "buying",
        "sell-to-us"
    ]
}

# =========================
# TICKET PANEL CHANNELS
# =========================

TICKET_PANEL_CHANNELS = [
    "tickets",
    "reports",
    "middleman-requests",
    "buying",
    "selling",
    "sell-to-us"
]

# Unique marker for Verify panels
TICKET_PANEL_MARKER = "VERIFY_TICKET_PANEL_V1"

# =========================
# HELPERS
# =========================

async def get_or_create_category(guild, name):

    category = discord.utils.get(
        guild.categories,
        name=name
    )

    if category:
        return category

    return await guild.create_category(name)


async def get_or_create_channel(category, name):

    channel = discord.utils.get(
        category.text_channels,
        name=name
    )

    if channel:
        return channel

    return await category.create_text_channel(name)


# =========================
# CHECK EXISTING PANEL
# =========================

async def ticket_panel_exists(channel):

    try:

        async for message in channel.history(limit=100):

            # Only check messages from Verify
            if message.author != bot.user:
                continue

            # Check embeds for our unique marker
            for embed in message.embeds:

                if embed.footer and embed.footer.text:

                    if embed.footer.text == TICKET_PANEL_MARKER:
                        return True

    except discord.Forbidden:

        print(
            f"❌ Cannot read #{channel.name}"
        )

        return False

    return False


# =========================
# CLOSE TICKET VIEW
# =========================

class CloseTicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close Ticket",
        emoji="🔒",
        style=discord.ButtonStyle.red,
        custom_id="ticket_close"
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild = interaction.guild

        if guild is None:
            return

        staff_role = discord.utils.get(
            guild.roles,
            name=STAFF_ROLE_NAME
        )

        # Only Staff can close tickets
        if staff_role and staff_role not in interaction.user.roles:

            await interaction.response.send_message(
                "❌ You don't have permission to close this ticket.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "🔒 Closing ticket in 5 seconds..."
        )

        await asyncio.sleep(5)

        try:

            await interaction.channel.delete(
                reason=f"Ticket closed by {interaction.user}"
            )

        except discord.NotFound:
            pass


# =========================
# CREATE TICKET VIEW
# =========================

class TicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Create Ticket",
        emoji="🎫",
        style=discord.ButtonStyle.green,
        custom_id="ticket_create"
    )
    async def create_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild = interaction.guild
        user = interaction.user

        if guild is None:
            return

        # =========================
        # FIND STAFF ROLE
        # =========================

        staff_role = discord.utils.get(
            guild.roles,
            name=STAFF_ROLE_NAME
        )

        if staff_role is None:

            await interaction.response.send_message(
                f"❌ Staff role `{STAFF_ROLE_NAME}` was not found.",
                ephemeral=True
            )

            return

        # =========================
        # FIND / CREATE TICKET CATEGORY
        # =========================

        category = discord.utils.get(
            guild.categories,
            name="Tickets"
        )

        if category is None:

            category = await guild.create_category(
                name="Tickets"
            )

        # =========================
        # PREVENT DUPLICATE TICKETS
        # =========================

        ticket_name = f"ticket-{user.id}"

        existing = discord.utils.get(
            category.text_channels,
            name=ticket_name
        )

        if existing:

            await interaction.response.send_message(
                f"❌ You already have a ticket: {existing.mention}",
                ephemeral=True
            )

            return

        # =========================
        # PRIVATE PERMISSIONS
        # =========================

        overwrites = {

            # Everyone else cannot see the ticket
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),

            # Ticket creator
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True
            ),

            # Staff
            staff_role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True,
                attach_files=True
            )
        }

        # =========================
        # CREATE TICKET
        # =========================

        channel = await guild.create_text_channel(
            ticket_name,
            category=category,
            overwrites=overwrites,
            reason=f"Ticket created by {user}"
        )

        # =========================
        # TICKET EMBED
        # =========================

        embed = discord.Embed(
            title="🎫 Support Ticket",
            description=(
                f"Welcome {user.mention}!\n\n"
                "Please describe your issue below.\n\n"
                "A staff member will assist you shortly.\n\n"
                "Use the button below when you are finished."
            ),
            color=discord.Color.blurple()
        )

        await channel.send(
            content=f"{user.mention} {staff_role.mention}",
            embed=embed,
            view=CloseTicketView()
        )

        # =========================
        # CONFIRMATION
        # =========================

        await interaction.response.send_message(
            f"✅ Your ticket has been created: {channel.mention}",
            ephemeral=True
        )


# =========================
# SETUP TICKET PANELS
# =========================

async def setup_ticket_panels(guild):

    """
    Makes sure every configured channel has
    exactly one official Verify ticket panel.
    """

    for channel_name in TICKET_PANEL_CHANNELS:

        # Find channel anywhere in the server
        channel = discord.utils.find(
            lambda c:
                isinstance(c, discord.TextChannel)
                and c.name == channel_name,
            guild.channels
        )

        if channel is None:

            print(
                f"⚠️ #{channel_name} not found"
            )

            continue

        # =========================
        # CHECK EXISTING PANEL
        # =========================

        exists = await ticket_panel_exists(channel)

        if exists:

            print(
                f"✓ Ticket panel already exists in #{channel_name}"
            )

            continue

        # =========================
        # CREATE PANEL
        # =========================

        embed = discord.Embed(
            title="🎫 Support Tickets",
            description=(
                "Need help?\n\n"
                "Click **Create Ticket** below to open "
                "a private support ticket.\n\n"
                "Only you and Staff will be able to see "
                "your ticket."
            ),
            color=discord.Color.blurple()
        )

        # Unique marker
        embed.set_footer(
            text=TICKET_PANEL_MARKER
        )

        await channel.send(
            embed=embed,
            view=TicketView()
        )

        print(
            f"✓ Ticket panel created in #{channel_name}"
        )


# =========================
# BOT
# =========================

class TicketBot(commands.Bot):

    def __init__(self):

        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):

        print(
            "Registering persistent ticket buttons..."
        )

        self.add_view(
            TicketView()
        )

        self.add_view(
            CloseTicketView()
        )

        print(
            "Persistent buttons registered."
        )


bot = TicketBot()


# =========================
# READY
# =========================

@bot.event
async def on_ready():

    print("=" * 50)

    print(
        f"Logged in as: {bot.user}"
    )

    print(
        f"Server ID: {GUILD_ID}"
    )

    print("=" * 50)

    guild = bot.get_guild(
        GUILD_ID
    )

    if guild is None:

        print(
            "❌ SERVER NOT FOUND"
        )

        print(
            "Check GUILD_ID and make sure the bot is in the server."
        )

        return

    print(
        f"Connected to: {guild.name}"
    )

    # =========================
    # CREATE SERVER STRUCTURE
    # =========================

    for category_name, channels in CHANNEL_STRUCTURE.items():

        category = await get_or_create_category(
            guild,
            category_name
        )

        print(
            f"\n📁 {category_name}"
        )

        for channel_name in channels:

            channel = await get_or_create_channel(
                category,
                channel_name
            )

            print(
                f"   ✓ #{channel.name}"
            )

    # =========================
    # CREATE TICKET CATEGORY
    # =========================

    ticket_category = discord.utils.get(
        guild.categories,
        name="Tickets"
    )

    if ticket_category is None:

        await guild.create_category(
            name="Tickets"
        )

        print(
            "📁 Tickets category created"
        )

    # =========================
    # AUTOMATICALLY SETUP PANELS
    # =========================

    await setup_ticket_panels(
        guild
    )

    # =========================
    # COMPLETE
    # =========================

    print(
        "\n" + "=" * 50
    )

    print(
        "SERVER SETUP COMPLETE"
    )

    print(
        "=" * 50
    )


# =========================
# SETUP TICKETS COMMAND
# =========================

@bot.command(name="setup_tickets")
@commands.has_permissions(administrator=True)
async def setup_tickets_command(ctx):

    # Make sure the command is being used in a server
    if ctx.guild is None:
        return

    await ctx.send(
        "🔧 Setting up ticket panels..."
    )

    try:

        await setup_ticket_panels(
            ctx.guild
        )

        await ctx.send(
            "✅ Ticket panels have been checked and set up!"
        )

    except discord.Forbidden:

        await ctx.send(
            "❌ I don't have permission to create/send messages in one or more channels."
        )

    except Exception as e:

        print(
            f"❌ Ticket setup error: {e}"
        )

        await ctx.send(
            "❌ An error occurred while setting up the ticket panels. Check the Railway logs."
        )


# =========================
# SETUP COMMAND ERROR
# =========================

@setup_tickets_command.error
async def setup_tickets_error(ctx, error):

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ You need Administrator permission to use this command."
        )

    else:

        print(
            f"❌ Setup command error: {error}"
        )

        await ctx.send(
            "❌ The command encountered an error."
        )


# =========================
# START
# =========================

bot.run(TOKEN)
