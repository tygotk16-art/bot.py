```python
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

        # Channel where the user pressed Create Ticket
        source_channel = interaction.channel

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
                f"**Ticket type:** {source_channel.mention}\n\n"
                f"This ticket was created from "
                f"{source_channel.mention}.\n\n"
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
```
