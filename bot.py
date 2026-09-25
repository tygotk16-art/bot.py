import os
import asyncio
import discord
from discord.ext import commands
# =========================
# CONFIG
# =========================

TOKEN = os.getenv("DISCORD_TOKEN")

# Put your Discord SERVER ID here
GUILD_ID = 1552705732481126480

# Change this if your staff role has a different name
STAFF_ROLE_NAME = "Staff"

# =========================
# BOT SETUP
# =========================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

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
# CHANNEL HELPERS
# =========================

async def get_or_create_category(guild, name):
    category = discord.utils.get(
        guild.categories,
        name=name
    )

    if category:
        return category

    return await guild.create_category(name=name)


async def get_or_create_channel(category, name):
    channel = discord.utils.get(
        category.text_channels,
        name=name
    )

    if channel:
        return channel

    return await category.create_text_channel(name=name)


# =========================
# CLOSE TICKET BUTTON
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

        staff_role = discord.utils.get(
            guild.roles,
            name=STAFF_ROLE_NAME
        )

        if staff_role and staff_role not in interaction.user.roles:
            await interaction.response.send_message(
                "You don't have permission to close this ticket.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🔒 Ticket will be closed in 5 seconds."
        )

        await asyncio.sleep(5)

        try:
            await interaction.channel.delete(
                reason=f"Ticket closed by {interaction.user}"
            )
        except discord.NotFound:
            pass


# =========================
# CREATE TICKET BUTTON
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

        # Find ticket category
        category = discord.utils.get(
            guild.categories,
            name="Tickets"
        )

        if category is None:
            category = await guild.create_category(
                name="Tickets"
            )

        # Check if user already has a ticket
        ticket_name = f"ticket-{user.id}"

        existing_ticket = discord.utils.get(
            category.text_channels,
            name=ticket_name
        )

        if existing_ticket:
            await interaction.response.send_message(
                f"❌ You already have a ticket: {existing_ticket.mention}",
                ephemeral=True
            )
            return

        # Permissions
        overwrites = {

            guild.default_role:
                discord.PermissionOverwrite(
                    view_channel=False
                ),

            user:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True
                ),

            staff_role:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_messages=True
                )
        }

        # Create ticket
        channel = await guild.create_text_channel(
            ticket_name,
            category=category,
            overwrites=overwrites,
            reason=f"Ticket created by {user}"
        )

        embed = discord.Embed(
            title="🎫 Support Ticket",
            description=(
                f"Welcome {user.mention}!\n\n"
                "Please describe your issue below.\n"
                "A staff member will help you shortly.\n\n"
                "When finished, use the button below to close "
                "the ticket."
            ),
            color=discord.Color.blurple()
        )

        await channel.send(
            content=f"{user.mention} {staff_role.mention}",
            embed=embed,
            view=CloseTicketView()
        )

        await interaction.response.send_message(
            f"✅ Ticket created: {channel.mention}",
            ephemeral=True
        )


# =========================
# READY EVENT
# =========================

@bot.event
async def on_ready():

    print("=" * 40)
    print(f"Logged in as: {bot.user}")
    print("=" * 40)

    guild = bot.get_guild(GUILD_ID)

    if guild is None:
        print("❌ Server not found.")
        print("Check your GUILD_ID.")
        return

    print(f"Setting up: {guild.name}")

    # -------------------------
    # CREATE CATEGORIES/CHANNELS
    # -------------------------

    for category_name, channels in CHANNEL_STRUCTURE.items():

        category = await get_or_create_category(
            guild,
            category_name
        )

        print(f"\n📁 {category_name}")

        for channel_name in channels:

            channel = await get_or_create_channel(
                category,
                channel_name
            )

            print(f"   ✓ #{channel.name}")

    # -------------------------
    # TICKET CATEGORY
    # -------------------------

    ticket_category = discord.utils.get(
        guild.categories,
        name="Tickets"
    )

    if ticket_category is None:

        ticket_category = await guild.create_category(
            name="Tickets"
        )

        print("📁 Created Tickets category")

    # -------------------------
    # TICKET PANEL
    # -------------------------

    ticket_channel = discord.utils.get(
        guild.text_channels,
        name="tickets"
    )

    if ticket_channel is None:
        print("❌ #tickets channel not found.")
        return

    # Check whether panel already exists
    panel_exists = False

    async for message in ticket_channel.history(
        limit=100
    ):

        if (
            message.author == bot.user
            and message.components
        ):
            panel_exists = True
            break

    if not panel_exists:

        embed = discord.Embed(
            title="🎫 Support Tickets",
            description=(
                "Need help?\n\n"
                "Click **Create Ticket** below to open "
                "a private support ticket.\n\n"
                "Please only create a ticket when you "
                "actually need assistance."
            ),
            color=discord.Color.blurple()
        )

        await ticket_channel.send(
            embed=embed,
            view=TicketView()
        )

        print("✓ Ticket panel created.")

    else:

        print("✓ Ticket panel already exists.")

    print("\n" + "=" * 40)
    print("SERVER SETUP COMPLETE")
    print("=" * 40)


# =========================
# PERSISTENT BUTTONS
# =========================

@bot.event
async def setup_hook():
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())


# =========================
# START BOT
# =========================

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN environment variable is not set."
    )

bot.run(TOKEN)
