import discord
from discord import app_commands
from discord.ext import commands
from zoneinfo import ZoneInfo, available_timezones
from .birthday_handling import *
from .variables import *


class confirmation_check(discord.ui.View):
    def __init__ (self):
        super().__init__(timeout=15)
        self.check_message = 0
    
    async def on_timeout(self):
        self.check_message = 2
        self.stop()
    
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, custom_id="confirm")
    async def on_confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.check_message = 1
        self.stop()
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, custom_id="reject")
    async def on_cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()


class override_commands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.months_list=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


    async def timezone_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=tz, value = tz)
            for tz in available_timezones()
            if current.lower() in tz.lower()
        ][:25]

    async def month_autocomplete(self, interaction: discord.Interaction, current: str):
        return[
            app_commands.Choice(name=mth, value=mth)
            for mth in self.months_list
            if current.lower() in mth.lower()
        ][:12]

    async def month_checker(self, date, month):
        if month in [4,6,9,11] and 1 <= date <= 30:
                return
        elif month == 2 and 1 <= date <= 29:
                return
        elif month in [1,3,5,7,8,10,12] and 1 <=  date <= 31:
                return
        raise Exception("Invalid date format. Try again.")

    override_group = app_commands.Group(name="override", description = "staff override commands")


    @override_group.command(name="add", description="Add a birthday to the database")
    @app_commands.describe(
        user="Select a user or provide their ID",
        day="Their birthday day (1-31)",
        month="Their birthday month (1-12)",
        timezone="Their IANA timezone (e.g. 'America/New_York')",
    )
    @app_commands.autocomplete(timezone = timezone_autocomplete)
    @app_commands.autocomplete(month = month_autocomplete)
    @app_commands.checks.has_any_role(professors, goblins)
    async def birthday(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        day: int,
        month: str,
        timezone: str = "UTC",
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            ZoneInfo(timezone)
        except Exception:
            await interaction.followup.send(
                "Invalid timezone. Please select one from the autocomplete list.\n"
                "You can find the IANA code at https://datetime.app/iana-timezones",
                ephemeral=True,
            )
            return

        try:
            for i in range(0,(len(self.months_list))):
                if month in self.months_list[i]:
                    month_int = i+1
                    break
            else:
                raise Exception("Month not found, enter the month properly.")
        except Exception as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
            return

        try:
            await self.month_checker(date=day, month=month_int)
        except Exception as e:
            await interaction.followup.send(f"Error: {e}")
            return

        view = confirmation_check()
        await interaction.followup.send(f"You are attempting to add a birthday entry for {user.mention} with date: {day}, month: {month}, and timezone: {timezone}. Proceed?", view=view)
        await view.wait()
        if view.check_message == 2:
            await interaction.edit_original_response(content="Interaction timed out. Please try again.", view=None)
            return
        if view.check_message == 0:
            await interaction.edit_original_response(content="Entry addition cancelled", view=None)
            return
        if view.check_message == 1:
            db = await init_db()
            async with db.execute("SELECT 1 FROM birthdays WHERE user_id = ?", (user.id,)) as cur:
                row = await cur.fetchone()
            if row:
                await interaction.edit_original_response(
                    content=f"{user.mention} already has a birthday entry. Use /birthday show to view.",
                    view=None
                )
                return
            try:
                await db.execute(
                    "INSERT INTO birthdays (user_id, month, day, timezone) VALUES (?,?,?,?)",
                    (user.id, month_int, day, timezone),
                    )
                await db.commit()
                await interaction.edit_original_response(
                    content=f"Added birthday for {user.mention} on {day} {month} in timezone {timezone}.",
                    view=None
                )
            except Exception as e:
                await interaction.edit_original_response(
                    content=f"Error entering data, please check for mistakes and try again.\n{e}", 
                    view=None
                    )


    @override_group.command(name="remove", description="Remove a birthday entry")
    @app_commands.describe(user="Select a user or provide their ID")
    @app_commands.checks.has_any_role(professors, goblins)
    async def remove_birthday(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
    ):
        await interaction.response.defer(ephemeral=True)
        view = confirmation_check()
        await interaction.followup.send(content=f"You are attempting to delete the birthday entry for {user.mention}. Proceed?", view=view)
        await view.wait()
        if view.check_message == 2:
            await interaction.edit_original_response(content="Interaction timed out. Please try again.", view=None)
            return
        if view.check_message == 0:
            await interaction.edit_original_response(content="Entry deletion cancelled.", view=None)
            return
        if view.check_message == 1:
            db = await init_db()
            async with db.execute("SELECT 1 FROM birthdays WHERE user_id = ?", (user.id,)) as cur:
                row = await cur.fetchone()
            if not row:
                await interaction.edit_original_response(
                    content=f"{user.mention} does not have a birthday entry.",
                    view=None
                )
                return
            await db.execute("DELETE FROM birthdays WHERE user_id = ?", (user.id,))
            await db.commit()
            await interaction.edit_original_response(
                content=f"Removed birthday entry for {user.mention}.",
                view=None
            )


    @override_group.command(name="force", description="Force a wish checking cycle to run")
    @app_commands.checks.has_any_role(professors, goblins)
    async def force_wish(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        handling_cog = self.bot.get_cog("birthday_handling")
        try:
            to_wish = await birthday_parser(self.bot)
            if to_wish:
                await handling_cog.wish_sender(to_wish)
        except Exception as e:
            print("error",e)
        await interaction.followup.send("Force wish cycle completed.", ephemeral=True)
            


async def setup(bot: commands.Bot):
    await init_db()
    cog = override_commands(bot)
    await bot.add_cog(cog)