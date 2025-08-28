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
            invalid_timezone_embed = discord.Embed(title="That's not a timezone...", 
                description="Invalid timezone. Please select one from the autocomplete list.\n"
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
                raise Exception("Month not found, enter the month properly.")
        except Exception as e:
            month_list_error=discord.Embed(title="Well, that didn't work.",
                description = f"{e}", 
                colour=discord.Colour.red())
            await interaction.followup.send(embed=month_list_error)
            return

        try:
            await self.month_checker(date=day, month=month_int)
        except Exception as e:
            month_check_error=discord.Embed(title="Well, that didn't work.", 
                            description = f"{e}", 
                            colour=discord.Colour.red())
            await interaction.followup.send(embed=month_check_error)
            return

        view = confirmation_check()
        confirmation_embed = discord.Embed(title="Are you sure?",
            description=f"You are attempting to add a birthday entry for {user.mention} with date: {day}, month: {month}, and timezone: {timezone}. Proceed?", 
            colour = interaction.user.colour)
        await interaction.followup.send(embed=confirmation_embed, view=view)
        await view.wait()

        if view.check_message == 2:
            timed_out_embed = discord.Embed(title="Too slow!",
                description="Interaction timed out. Please try again.", 
                colour=discord.Colour.red())
            await interaction.edit_original_response(embed=timed_out_embed, view=None)
            return

        if view.check_message == 0:
            cancelled_addition_embed = discord.Embed(title="Someone's indecisive!",
                description="Entry addition cancelled", 
                colour=discord.Colour.red())
            await interaction.edit_original_response(embed=cancelled_addition_embed, view=None)
            return

        if view.check_message == 1:
            db = await init_db()
            async with db.execute("SELECT 1 FROM birthdays WHERE user_id = ?", (user.id,)) as cur:
                row = await cur.fetchone()
            if row:
                existing_birthday_embed = discord.Embed(title="There's something in the way...",
                    description=f"{user.mention} already has a birthday entry. Use /birthday show to view.", 
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
                    description=f"Added birthday for {user.mention} on {day} {month} in timezone {timezone}.", 
                    colour=discord.Colour.green())
                await interaction.edit_original_response(embed=add_success_embed, view=None)
            except Exception as e:
                entry_error_embed=discord.Embed(title="Well, that didn't work.",
                    description=f"Error entering data, please check for mistakes and try again.\n{e}", 
                    colour=discord.Colour.red())
                await interaction.edit_original_response(embed=entry_error_embed, view=None)


    @override_group.command(name="remove", description="Remove a birthday from the database")
    @app_commands.describe(user="Select a user or provide their ID")
    @app_commands.checks.has_any_role(professors, goblins)
    async def remove_birthday(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
    ):
        await interaction.response.defer(ephemeral=True)
        view = confirmation_check()
        check_embed = discord.Embed(title="Are you sure?",
            description=f"You are attempting to delete the birthday entry for {user.mention}. Proceed?", 
            colour=interaction.user.colour)
        await interaction.followup.send(embed=check_embed, view=view)
        await view.wait()

        if view.check_message == 2:
            timeout_embed = discord.Embed(title="Too slow!",
            description="Interaction timed out!", 
            colour=discord.Colour.red())
            await interaction.edit_original_response(embed=timeout_embed, view=None)
            return

        if view.check_message == 0:
            cancel_embed = discord.Embed(title="Someone's Indecisive!",
            description="Entry deletion cancelled.", 
            colour=discord.Colour.red())
            await interaction.edit_original_response(embed=cancel_embed, view=None)
            return

        if view.check_message == 1:
            db = await init_db()
            async with db.execute("SELECT 1 FROM birthdays WHERE user_id = ?", (user.id,)) as cur:
                row = await cur.fetchone()
            if not row:
                no_birthday_embed = discord.Embed(title="Such empty...",
                    description=f"{user.mention} doesn't have a birthday entry.", 
                    colour=discord.Colour.red())
                await interaction.edit_original_response(embed=no_birthday_embed, view=None)
                return
            await db.execute("DELETE FROM birthdays WHERE user_id = ?", (user.id,))
            await db.commit()
            removal_success_embed = discord.Embed(title="Oh look! It worked!",
                description=f"Removed birthday entry for {user.mention}.", 
                colour=discord.Colour.green())
            await interaction.edit_original_response(embed=removal_success_embed, view=None)


    @override_group.command(name="force", description="Force a wish checking cycle to run")
    @app_commands.checks.has_any_role(professors, goblins)
    async def force_wish(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        handling_cog = self.bot.get_cog("birthday_handling")
        to_wish = await birthday_parser(self.bot)
        if to_wish:
            await handling_cog.wish_sender(to_wish)
        await interaction.followup.send("Force wish cycle completed.")
    

    @override_group.command(name="status", description="Displays the nearest past and upcoming (registered) birthdays and the size of the database")
    @app_commands.checks.has_any_role(professors, goblins)
    async def db_status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        db = await init_db()
        guild = self.bot.get_guild(guild_id) or await self.bot.fetch_guild(guild_id)
        status_embed = discord.Embed(title="Database status information", 
                                     description="The nearest past and upcoming (registered) birthdays, and the size of the database.",
                                     colour=interaction.user.colour)
        today = datetime.now(timezone.utc)
        today_day, today_month = today.day, today.month

        async with db.execute("""
                              SELECT user_id, day, month
                              FROM birthdays
                              WHERE (month < ?) OR (month = ? AND day <= ?)
                              ORDER BY month DESC, day DESC
                              LIMIT 1
                              """, (today_month, today_month, today_day)
        ) as cur:
            row = await cur.fetchone()
            if not row:
                status_embed.add_field(name="Such empty...",
                                       value="There have been no birthdays so far this year.",
                                       inline=False)
                pass
            else:
                recent_user, recent_day, recent_month = row
                recent_user_object = guild.get_member(recent_user) or await guild.fetch_member(recent_user)
                status_embed.add_field(name="Most recent birthday",
                                       value=f"{recent_user_object.mention} on {recent_day} {self.months_list[recent_month-1]}",
                                       inline=False)
                pass
        
        async with db.execute("""
                              SELECT user_id, day, month
                              FROM birthdays
                              WHERE (month > ?) OR (month = ? AND day >= ?)
                              ORDER BY month ASC, day ASC
                              LIMIT 1
                              """, (today_month, today_month, today_day)
        ) as cur:
            row =  await cur.fetchone()
            if not row:
                status_embed.add_field(name="Such empty...",
                                       value="There are no more birthdays this year.",
                                       inline=False)
                pass
            else:
                upcoming_user, upcoming_day, upcoming_month = row
                upcoming_user_object = guild.get_member(upcoming_user) or await guild.fetch_member(upcoming_user)
                status_embed.add_field(name="Closest upcoming birthday",
                                       value=f"{upcoming_user_object.mention} on {upcoming_day} {self.months_list[upcoming_month-1]}",
                                       inline=False)
                pass
        
        async with db.execute("SELECT user_id from birthdays") as cur:
            row = await cur.fetchall()
            if not row:
                status_embed.add_field(name="Such empty...",
                                       value="There are no birthdays stored", 
                                       inline=False)
                pass
            else:
                db_size = len(row)
                status_embed.add_field(name="Database Size",
                                       value=f"There are {db_size} birthdays stored in the database",
                                       inline=False)
                pass
        await interaction.followup.send(embed=status_embed)


async def setup(bot: commands.Bot):
    await init_db()
    cog = override_commands(bot)
    await bot.add_cog(cog)