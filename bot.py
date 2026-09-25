import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

# Optional: put your server ID here to prevent accidentally running
# the setup on the wrong server.
GUILD_ID = 123456789012345678

# Replace this with your staff role name
STAFF_ROLE_NAME = "Staff"

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


CHANNEL_STRUCTURE = {
    "Information": [
        "rules",
        "announcements",
    ],

    "Marketplace": [
        "buying",
        "selling",
        "vouches",
        "middleman-requests",
    ],

    "Support": [
        "tickets",
        "reports",
    ],

    "Staff": [
        "staff-chat",
        "logs",
        "📜-ticket-logs",
    ],

    "DONUT SMP": [
        "buying",
        "sell-to-us",
    ],
}


async def get_or_create_category(guild, name):
    category = discord.utils.get(guild.categories, name=name)

    if category:
        return category

    return await guild.create_category(name)


async def get_or_create_channel(category, name):
    channel = discord.utils.get(category.text_channels, name=name)

    if channel:
        return channel

    return await category.create_text_channel(name)


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Create Ticket",
        style=discord.ButtonStyle.green,
        emoji="🎫",
        custom_id="create_ticket"
    )
    async def create_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        guild = interaction.guild

        staff_role = discord.utils.get(
            guild.roles,
            name=STAFF_ROLE_NAME
        )

        if not staff_role:
            await interaction.response.send_message(
                f"Staff role `{STAFF_ROLE_NAME}` was not found.",
                ephemeral=True
            )
            return

        # Prevent multiple tickets from the same user
        existing = discord.utils.find(
            lambda c: c.name == f"ticket-{interaction.user.id}",
            guild.text_channels
        )

        if existing:
            await interaction.response.send_message(
                f"You already have a ticket: {existing.mention}",
                ephemeral=True
            )
            return

        category = discord.utils.get(
            guild.categories,
            name="Tickets"
        )

        if category is None:
            category = await guild.create_category("Tickets")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),

            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True
            ),

            staff_role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True
            )
        }

        channel = await guild.create_text_channel(
            f"ticket-{interaction.user.id}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎫 Support Ticket",
            description=(
                f"Welcome {interaction.user.mention}!\n\n"
                "Please explain your issue and a staff member "
                "will assist you shortly."
            ),
            color=discord.Color.blurple()
        )

        await channel.send(
            content=f"{interaction.user.mention} {staff_role.mention}",
            embed=embed,
            view=CloseTicketView()
        )

        await interaction.response.send_message(
            f"Your ticket has been created: {channel.mention}",
            ephemeral=True
        )


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.red,
        emoji="🔒",
        custom_id="close_ticket"
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        guild = interaction.guild
        channel = interaction.channel

        staff_role = discord.utils.get(
            guild.roles,
            name=STAFF_ROLE_NAME
        )

        # Only staff can close tickets
        if staff_role not in interaction.user.roles:
            await interaction.response.send_message(
                "You don't have permission to close tickets.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🔒 Closing ticket in 5 seconds..."
        )

        await discord.utils.sleep_until(
            discord.utils.utcnow() + discord.utils.timedelta(seconds=5)
        )

        await channel.delete()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    guild = bot.get_guild(GUILD_ID)

    if guild is None:
        print("Guild not found. Check GUILD_ID.")
        return

    print(f"Setting up: {guild.name}")

    # Create all requested categories/channels
    for category_name, channels in CHANNEL_STRUCTURE.items():

        category = await get_or_create_category(
            guild,
            category_name
        )

        for channel_name in channels:
            channel = await get_or_create_channel(
                category,
                channel_name
            )

            print(f"✓ {category_name} / #{channel.name}")

    # Add ticket category used for individual tickets
    ticket_category = discord.utils.get(
        guild.categories,
        name="Tickets"
    )

    if ticket_category is None:
        ticket_category = await guild.create_category("Tickets")

    # Find the ticket panel channel
    ticket_channel = discord.utils.get(
        guild.text_channels,
        name="tickets"
    )

    if ticket_channel:
        # Don't spam multiple panels every restart.
        async for message in ticket_channel.history(limit=50):
            if (
                message.author == bot.user
                and message.components
            ):
                print("✓ Ticket panel already exists.")
                break
        else:
            embed = discord.Embed(
                title="🎫 Support Tickets",
                description=(
                    "Need help?\n\n"
                    "Click the button below to create a private "
                    "support ticket.\n\n"
                    "A staff member will assist you as soon as possible."
                ),
                color=discord.Color.blurple()
            )

            await ticket_channel.send(
                embed=embed,
                view=TicketView()
            )

            print("✓ Ticket panel created.")

    print("================================")
    print("Server setup completed.")
    print("================================")


# Persistent buttons
bot.add_view(TicketView())
bot.add_view(CloseTicketView())

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN environment variable is missing."
    )

bot.run(TOKEN)
