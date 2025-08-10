import discord
from discord import app_commands
from discord.ext import commands
import re
import asyncio
from zoneinfo import ZoneInfo
from main import BirthdayBot
from birthday_handling import (
    init_db,
    birthay_parser,
    mark_sent,
    build_timezone_choices,
    guild_id,
)



gryffindor_role = 524558749512499230
hufflepuff_role = 524558390316498944
ravenclaw_role = 524558868383137812
slytherin_role = 524558928898424833

clock_tower = 825789506019000320

professors = 731429277563748412
goblins = 526069180831891467
poltergeists = 1345448742022545510


class birthday_handling(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def wish_sender(self, to_wish):
        guild = self.bot.get_guild(guild_id) or await self.bot.fetch_guild(guild_id)

        for i in to_wish:
            birthday_member = guild.get_member(i) or await guild.fetch_member(i)

            if any(r.id == gryffindor_role for r in birthday_member.roles):
                role = guild.get_role(gryffindor_role)
                wish_colour = (role and role.color) or discord.Colour.from_str("#c80752")
            elif any(r.id == hufflepuff_role for r in birthday_member.roles):
                role = guild.get_role(hufflepuff_role)
                wish_colour = (role and role.color) or discord.Colour.from_str("#ffd046")
            elif any(r.id == ravenclaw_role for r in birthday_member.roles):
                role = guild.get_role(ravenclaw_role)
                wish_colour = (role and role.color) or discord.Colour.from_str("#4d90cd")
            elif any(r.id == slytherin_role for r in birthday_member.roles):
                role = guild.get_role(slytherin_role)
                wish_colour = (role and role.color) or discord.Colour.from_str("#006351")
            else:
                continue

            birthday_embed = discord.Embed(colour=wish_colour)
            channel = guild.get_channel(clock_tower) or await guild.fetch_channel(clock_tower)
            await channel.send(
                birthday_member.mention,
                embed=birthday_embed,
                allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
            )

        await mark_sent(to_wish)

    async def wish_checker(self, bot: commands.Bot):
        while True:
            try:
                to_wish = await birthay_parser(bot)
                if to_wish:
                    await self.wish_sender(to_wish)
            except Exception:
                pass
            await asyncio.sleep(900)


    @app_commands.command(name="add_birthday", description="Add a birthday to the database")
    @app_commands.describe(
        user="Select a user or provide their ID",
        month="Their birthday month (1-12)",
        day="Their birthday day (1-31)",
        timezone="Their IANA timezone (e.g. 'America/New_York')",
    )
    @app_commands.checks.has_any_role(professors, goblins, poltergeists)
    async def birthday(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        month: int,
        day: int,
        timezone: str = "UTC",
    ):
        try:
            ZoneInfo(timezone)
        except Exception:
            await interaction.response.send_message(
                "Invalid timezone. Please select one from the autocomplete list.",
                ephemeral=True,
            )
            return

        db = await init_db()

        async with db.execute("SELECT 1 FROM birthdays WHERE user_id = ?", (user.id,)) as cur:
            row = await cur.fetchone()
        if row:
            await interaction.response.send_message(
                f"{user.mention} already has a birthday entry.",
                ephemeral=True,
            )
            return

        await db.execute(
            "INSERT INTO birthdays (user_id, month, day, timezone) VALUES (?,?,?,?)",
            (user.id, month, day, timezone),
        )
        await db.commit()

        await interaction.response.send_message(
            f"Added birthday for {user.mention} on {month}/{day} in timezone {timezone}.",
            ephemeral=True,
        )

    @birthday.autocomplete("timezone")
    async def birthday_timezone_ac(self, interaction: discord.Interaction, current: str):
        pairs = await build_timezone_choices(current)
        return [app_commands.Choice(name=name, value=value) for name, value in pairs]


    @app_commands.command(name="edit_birthday", description="Edit an existing birthday entry")
    @app_commands.describe(
        user="select a user or provide their ID",
        month="Their birthday month (1-12)",
        day="Their birthday day (1-31)",
        timezone="Their IANA timezone (e.g. 'America/New_York')",
    )
    @app_commands.checks.has_any_role(professors, goblins, poltergeists)
    async def edit_birthday(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        month: int,
        day: int,
        timezone: str = "UTC",
    ):
        try:
            ZoneInfo(timezone)
        except Exception:
            await interaction.response.send_message(
                "Invalid timezone. Please select one from the autocomplete list.",
                ephemeral=True,
            )
            return

        db = await init_db()

        async with db.execute("SELECT 1 FROM birthdays WHERE user_id = ?", (user.id,)) as cur:
            row = await cur.fetchone()
        if not row:
            await interaction.response.send_message(
                f"{user.mention} does not have a birthday entry.",
                ephemeral=True,
            )
            return

        await db.execute(
            """
            UPDATE birthdays
            SET month = ?, day = ?, timezone = ?
            WHERE user_id = ?
            """,
            (month, day, timezone, user.id),
        )
        await db.commit()

        await interaction.response.send_message(
            f"Updated birthday for {user.mention} to {month}/{day} in timezone {timezone}.",
            ephemeral=True,
        )

    @edit_birthday.autocomplete("timezone")
    async def edit_timezone_ac(self, interaction: discord.Interaction, current: str):
        pairs = await build_timezone_choices(current)
        return [app_commands.Choice(name=name, value=value) for name, value in pairs]


    @app_commands.command(name="remove_birthday", description="Remove a birthday entry")
    @app_commands.describe(user="Select a user or provide their ID")
    @app_commands.checks.has_any_role(professors, goblins, poltergeists)
    async def remove_birthday(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
    ):
        db = await init_db()

        async with db.execute("SELECT 1 FROM birthdays WHERE user_id = ?", (user.id,)) as cur:
            row = await cur.fetchone()
        if not row:
            await interaction.response.send_message(
                f"{user.mention} does not have a birthday entry.",
                ephemeral=True,
            )
            return

        await db.execute("DELETE FROM birthdays WHERE user_id = ?", (user.id,))
        await db.commit()

        await interaction.response.send_message(
            f"Removed birthday entry for {user.mention}.",
            ephemeral=True,
        )


    @app_commands.command(name="show_birthday", description="Show a user's birthday information")
    @app_commands.describe(user="Select a user or provide their ID")
    async def show_birthday(
        self,
        interaction: discord.Interaction, 
        user= discord.Member
    ):
        db = await init_db()
        async with db.execute("SELECT month, day FROM birthdays WHERE user_id = ?", (user.id,)) as cur:
            row  = await cur.fetchone()
            if not row:
                await interaction.response.send_message(
                    f"{user.mention} does not have a birthday entry. Contact your nearest poltergeist to add one.", 
                    ephemeral=True)
            for month, day in row:
                await interaction.response.send_message(
                    f"{user.mention}'s birthday is on {day}/{month}.", ephemeral=True)


    @app_commands.command(name="force_wish", description="Force a wish checking cycle to run")
    @app_commands.checks.has_any_role(professors, goblins)
    async def force_wish(self, interaction: discord.Interaction):
        while True:
            try:
                to_wish = await birthay_parser(self.bot)
                if to_wish:
                    await self.wish_sender(to_wish)
            except Exception:
                pass


async def setup(bot: BirthdayBot):
    await init_db()
    cog = birthday_handling(bot)
    await bot.add_cog(cog)

    async def _start_loop():
        await bot.wait_until_ready()
        bot.loop.create_task(cog.wish_checker(bot))

    bot.loop.create_task(_start_loop())
