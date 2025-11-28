import discord
import datetime as dt
from discord import app_commands
from discord.ext import commands
from zoneinfo import ZoneInfo, available_timezones
from .birthday_handling import *
from .variables import *


class confirmation_check(discord.ui.View):
    def __init__ (self):
        super().__init__(timeout=45)
        self.check_message = 2
    
    async def on_timeout(self):
        self.check_message = 2
        self.stop()
    
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, custom_id="confirm", emoji=approve_tick_emoji)
    async def on_confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        self.check_message = 1
        self.stop()
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, custom_id="reject", emoji=alert_emoji)
    async def on_cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        self.check_message = 0
        self.stop()


def override_access():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id == tairneanach:
            return True
        if interaction.user.id == professors:
            return True
        return False
    return app_commands.check(predicate=predicate)


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
        raise Exception(f"{alert_emoji} Invalid date format. Try again.")

    override_group = app_commands.Group(name="override", description= "admin override commands")

    @override_group.command(name="add", description="[Admin only] Add a birthday to the database")
    @override_access()
    @app_commands.describe(
        user="Select a user or provide their ID",
        day="Their birthday day (1-31)",
        month="Their birthday month (1-12)",
        timezone="Their IANA timezone (e.g. 'America/New_York')",
    )
    @app_commands.autocomplete(timezone = timezone_autocomplete)
    @app_commands.autocomplete(month = month_autocomplete)
    async def add_birthday(
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
            invalid_timezone_embed = discord.Embed(title="That's not a timezone...", 
                description=f"{alert_emoji} Invalid timezone. Please select one from the autocomplete list.\n"
                "You can find the IANA code at https://datetime.app/iana-timezones",
                colour=discord.Colour.red())
            await interaction.followup.send(embed=invalid_timezone_embed)
            return

        try:
            for i in range(0,(len(self.months_list))):
                if month in self.months_list[i]:
                    month_int = i+1
                    break
            else:
                raise Exception(f"{alert_emoji} Month not found, enter the month properly.")
        except Exception as e:
            month_list_error=discord.Embed(title="Well, that didn't work.",
                description = f"{alert_emoji} {e}", 
                colour=discord.Colour.red())
            await interaction.followup.send(embed=month_list_error)
            return

        try:
            await self.month_checker(date=day, month=month_int)
        except Exception as e:
            month_check_error=discord.Embed(title="Well, that didn't work.", 
                            description = f"{alert_emoji} {e}", 
                            colour=discord.Colour.red())
            await interaction.followup.send(embed=month_check_error)
            return

        view = confirmation_check()
        now_ts  = dt.datetime.now(dt.timezone.utc).timestamp()
        confirmation_embed = discord.Embed(title="Are you sure?",
            description=f"{alert_emoji} You are attempting to add a birthday entry for {user.mention} with date: {day}, month: {month}, and timezone: {timezone}. Proceed?\n"
            f"-# This interaction will time out <t:{int(now_ts+45)}:R>", 
            colour = interaction.user.colour)
        await interaction.followup.send(embed=confirmation_embed, view=view)
        await view.wait()

        if view.check_message == 2:
            timed_out_embed = discord.Embed(title="Too slow!",
                description=f"{alert_emoji} Interaction timed out. Please try again.", 
                colour=discord.Colour.red())
            await interaction.edit_original_response(embed=timed_out_embed, view=None)
            return

        if view.check_message == 0:
            cancelled_addition_embed = discord.Embed(title="Someone's indecisive!",
                description=f"{alert_emoji} Entry addition cancelled", 
                colour=discord.Colour.red())
            await interaction.edit_original_response(embed=cancelled_addition_embed, view=None)
            return

        if view.check_message == 1:

            if timezone in "UTC":

                now_ts  = dt.datetime.now(dt.timezone.utc).timestamp()
                timezone_confirmation_embed=discord.Embed(title="Wish at midnight UTC?",
                    description=f"{alert_emoji} The user will be wished at around midnight UTC on the day of their birthday.\n"
                    "If you would like for them to be wished in their local timezone, find its IANA code at https://datetime.app/iana-timezones and enter it in the command's 'timezone' field.\n"
                    "If you would like to proceed with UTC, press confirm.\n"
                    f"-# This interaction will time out <t:{int(now_ts+45)}:R>",
                    colour=interaction.user.colour)
                view = confirmation_check()
                await interaction.edit_original_response(embed=timezone_confirmation_embed, view=view)
                await view.wait()

                if view.check_message == 2:
                    timed_out_embed = discord.Embed(title="Too slow!",
                        description=f"{alert_emoji} Interaction timed out. Please try again.", 
                        colour=discord.Colour.red())
                    await interaction.edit_original_response(embed=timed_out_embed, view=None)
                    return

                if view.check_message == 0:
                    cancelled_addition_embed = discord.Embed(title="Someone's indecisive!",
                        description=f"{alert_emoji} Entry addition cancelled", 
                        colour=discord.Colour.red())
                    await interaction.edit_original_response(embed=cancelled_addition_embed, view=None)
                    return

                if view.check_message == 1:
                    pass

            db = await init_db()
            async with db.execute("SELECT 1 FROM birthdays WHERE user_id = ?", (user.id,)) as cur:
                row = await cur.fetchone()
            if row:
                existing_birthday_embed = discord.Embed(title="There's something in the way...",
                    description=f"{alert_emoji} {user.mention} already has a birthday entry. Use /birthday show to view.", 
                    colour=discord.Colour.red())
                await interaction.edit_original_response(embed=existing_birthday_embed, view=None)
                return

            try:
                await db.execute(
                    "INSERT INTO birthdays (user_id, month, day, timezone) VALUES (?,?,?,?)",
                    (user.id, month_int, day, timezone),
                    )
                await db.commit()
                add_success_embed  = discord.Embed(title="Oh look! It worked!",
                    description=f"{approve_tick_emoji} Added birthday for {user.mention} on {day} {month} in the {timezone} timezone.", 
                    colour=discord.Colour.green())
                await interaction.edit_original_response(embed=add_success_embed, view=None)
            except Exception as e:
                entry_error_embed=discord.Embed(title="Well, that didn't work.",
                    description=f"{alert_emoji} Error entering data, please check for mistakes and try again.\n{e}", 
                    colour=discord.Colour.red())
                await interaction.edit_original_response(embed=entry_error_embed, view=None)


    @override_group.command(name="remove", description="[Admin only] Remove a birthday from the database")
    @override_access()
    @app_commands.describe(user="Select a user or provide their ID")
    async def remove_birthday(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
    ):
        await interaction.response.defer(ephemeral=True)
        view = confirmation_check()
        now_ts  = dt.datetime.now(dt.timezone.utc).timestamp()
        check_embed = discord.Embed(title="Are you sure?",
            description=f"{alert_emoji} You are attempting to delete the birthday entry for {user.mention}. Proceed?\n"
            f"-# This interaction will time out <t:{int(now_ts+45)}:R>", 
            colour=interaction.user.colour)
        await interaction.followup.send(embed=check_embed, view=view)
        await view.wait()

        if view.check_message == 2:
            timeout_embed = discord.Embed(title="Too slow!",
            description=f"{alert_emoji} Interaction timed out!", 
            colour=discord.Colour.red())
            await interaction.edit_original_response(embed=timeout_embed, view=None)
            return

        if view.check_message == 0:
            cancel_embed = discord.Embed(title="Someone's Indecisive!",
            description=f"{alert_emoji} Entry deletion cancelled.", 
            colour=discord.Colour.red())
            await interaction.edit_original_response(embed=cancel_embed, view=None)
            return

        if view.check_message == 1:
            db = await init_db()
            async with db.execute("SELECT 1 FROM birthdays WHERE user_id = ?", (user.id,)) as cur:
                row = await cur.fetchone()
            if not row:
                no_birthday_embed = discord.Embed(title="Such empty...",
                    description=f"{alert_emoji} {user.mention} doesn't have a birthday entry.", 
                    colour=discord.Colour.red())
                await interaction.edit_original_response(embed=no_birthday_embed, view=None)
                return
            await db.execute("DELETE FROM birthdays WHERE user_id = ?", (user.id,))
            await db.commit()
            removal_success_embed = discord.Embed(title="Oh look! It worked!",
                description=f"{approve_tick_emoji} Removed birthday entry for {user.mention}.", 
                colour=discord.Colour.green())
            await interaction.edit_original_response(embed=removal_success_embed, view=None)


async def setup(bot: commands.Bot):
    await init_db()
    cog = override_commands(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.override_group)
    except app_commands.CommandAlreadyRegistered:
        pass