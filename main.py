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
# HELPERS
# =========================

async def get_or_create_category(guild, name):
    category = discord.utils.get(guild.categories, name=name)

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
    async def create_ticket(self, interaction, button):
        guild = interaction.guild
        user = interaction.user

        if guild is None:
            return

        # Find Staff role
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

        # Find or create Tickets category
        category = discord.utils.get(
            guild.categories,
            name="Tickets"
        )

        if category is None:
            category = await guild.create_category(
                name="Tickets"
            )

        # Prevent duplicate tickets
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

        # Only:
        # - Ticket creator
        # - Staff
        # can see the ticket.
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),

            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True
            ),

            staff_role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True,
                attach_files=True
            )
        }

        # Create private ticket
        channel = await guild.create_text_channel(
            ticket_name,
            category=category,
            overwrites=overwrites,
            reason=f"Ticket created by {user}"
        )

        # Ticket message
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

        await interaction.response.send_message(
            f"✅ Your ticket has been created: {channel.mention}",
            ephemeral=True
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
        print("Registering persistent ticket buttons...")

        self.add_view(TicketView())
        self.add_view(CloseTicketView())

        print("Persistent buttons registered.")


bot = TicketBot()


# =========================
# READY
# =========================

@bot.event
async def on_ready():

    print("=" * 50)
    print(f"Logged in as: {bot.user}")
    print(f"Server ID: {GUILD_ID}")
    print("=" * 50)

    guild = bot.get_guild(GUILD_ID)

    if guild is None:
        print("❌ SERVER NOT FOUND")
        print("Check GUILD_ID and make sure the bot is in the server.")
        return

    print(f"Connected to: {guild.name}")

    # Create normal server structure

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

    # Create ticket category

    ticket_category = discord.utils.get(
        guild.categories,
        name="Tickets"
    )

    if ticket_category is None:
        ticket_category = await guild.create_category(
            name="Tickets"
        )

        print("📁 Tickets category created")

    # Find ticket panel channel

    ticket_channel = discord.utils.get(
        guild.text_channels,
        name="tickets"
    )

    if ticket_channel is None:
        print("❌ #tickets channel not found.")
        return

    # Check for existing panel

    panel_exists = False

    try:
        async for message in ticket_channel.history(limit=100):

            if (
                message.author == bot.user
                and message.components
            ):
                panel_exists = True
                break

    except discord.Forbidden:
        print("❌ Bot cannot read #tickets.")
        return

    # Create panel

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

        print("✓ Ticket panel created")

    else:
        print("✓ Ticket panel already exists")

    print("\n" + "=" * 50)
    print("SERVER SETUP COMPLETE")
    print("=" * 50)


# =========================
# START
# =========================

bot.run(TOKEN)
