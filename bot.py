@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    guild = ctx.guild

    # Categories
    tickets_category = discord.utils.get(guild.categories, name="📂 Tickets")
    if tickets_category is None:
        tickets_category = await guild.create_category("📂 Tickets")

    active_category = discord.utils.get(guild.categories, name="📂 Active Tickets")
    if active_category is None:
        active_category = await guild.create_category("📂 Active Tickets")

    # Logs
    logs = discord.utils.get(guild.text_channels, name="📜-ticket-logs")
    if logs is None:
        await guild.create_text_channel("📜-ticket-logs")

    channels = {
        "🎫︱buying-ticket": "Open Buying Ticket",
        "💰︱selling-ticket": "Open Selling Ticket",
        "🤝︱middleman-ticket": "Request Middleman",
        "⚠️︱report-ticket": "Open Report Ticket",
        "📝︱application-ticket": "Open Application Ticket",
        "❓︱support-ticket": "Open Support Ticket"
    }

    for channel_name in channels:
        channel = discord.utils.get(guild.text_channels, name=channel_name)

        if channel is None:
            channel = await guild.create_text_channel(
                channel_name,
                category=tickets_category
            )

        await channel.purge(limit=20)

        embed = discord.Embed(
            title=channel_name,
            description="Press the button below to open a private ticket.",
            color=discord.Color.blue()
        )

        view = discord.ui.View()

        async def button_callback(interaction, cname=channel_name):
            active = discord.utils.get(
                interaction.guild.categories,
                name="📂 Active Tickets"
            )

            overwrites = {
                interaction.guild.default_role:
                    discord.PermissionOverwrite(view_channel=False),

                interaction.user:
                    discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True
                    )
            }

            for role_name in ["🛠 Admin", "🔨 Moderator"]:
                role = discord.utils.get(
                    interaction.guild.roles,
                    name=role_name
                )

                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        manage_channels=True
                    )

            ticket = await interaction.guild.create_text_channel(
                name=f"ticket-{interaction.user.name}",
                category=active,
                overwrites=overwrites
            )

            await ticket.send(
                f"{interaction.user.mention} welcome to your ticket."
            )

            await interaction.response.send_message(
                f"Ticket created: {ticket.mention}",
                ephemeral=True
            )

        button = discord.ui.Button(
            label=channels[channel_name],
            style=discord.ButtonStyle.green
        )

        button.callback = button_callback
        view.add_item(button)

        await channel.send(embed=embed, view=view)

    await ctx.send("✅ Ticket system created.")
