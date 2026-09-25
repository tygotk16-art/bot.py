import discord
from discord.ext import commands

TOKEN = "MTU1MzA3NjAwMjI5OTcxNTY3NA.GMq25D.1k7z69ilROU77umDyV6XgVu-EsHxrFjS5VbkY8"

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_trade_server(ctx):
    guild = ctx.guild

    # Roles
    roles = [
        "👑 Owner",
        "🛠 Admin",
        "🔨 Moderator",
        "💰 Seller",
        "✅ Trusted",
        "🛒 Customer",
        "🤖 Bots"
    ]

    for role_name in roles:
        if not discord.utils.get(guild.roles, name=role_name):
            await guild.create_role(name=role_name)

    # Categories
    categories = [
        "📋 Information",
        "🛒 Marketplace",
        "🎫 Tickets",
        "🔒 Staff",
        "📊 Logs"
    ]

    created = {}

    for category_name in categories:
        category = discord.utils.get(guild.categories, name=category_name)

        if category is None:
            category = await guild.create_category(category_name)

        created[category_name] = category

    # Information
    for channel in [
        "rules",
        "announcements",
        "faq"
    ]:
        if not discord.utils.get(guild.text_channels, name=channel):
            await guild.create_text_channel(
                channel,
                category=created["📋 Information"]
            )

    # Marketplace
    for channel in [
        "buying",
        "selling",
        "vouches",
        "completed-trades",
        "middleman-requests"
    ]:
        if not discord.utils.get(guild.text_channels, name=channel):
            await guild.create_text_channel(
                channel,
                category=created["🛒 Marketplace"]
            )

    # Ticket Channels
    for channel in [
        "create-ticket",
        "ticket-logs"
    ]:
        if not discord.utils.get(guild.text_channels, name=channel):
            await guild.create_text_channel(
                channel,
                category=created["🎫 Tickets"]
            )

    # Staff
    for channel in [
        "staff-chat",
        "staff-logs",
        "reports"
    ]:
        if not discord.utils.get(guild.text_channels, name=channel):
            await guild.create_text_channel(
                channel,
                category=created["🔒 Staff"]
            )

    await ctx.send("✅ Server structure created.")

bot.run(TOKEN)
