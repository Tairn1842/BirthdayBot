import discord, re, asyncio, random
from discord import app_commands
from discord.ext import commands
from zoneinfo import ZoneInfo, available_timezones
from .birthday_handling import *
from .wish_generator import wish_creator


gryffindor_role = 524558749512499230
hufflepuff_role = 524558390316498944
ravenclaw_role = 524558868383137812
slytherin_role = 524558928898424833

test_role = 1382637708236685375
test_channel = 1402297966953369610

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
            avatar_url = birthday_member.avatar.url

            if any(r.id == gryffindor_role for r in birthday_member.roles):
                role = guild.get_role(gryffindor_role)
                house = 1
                wish_colour = (role and role.color) or discord.Colour.from_str("#740001")
            elif any(r.id == hufflepuff_role for r in birthday_member.roles):
                role = guild.get_role(hufflepuff_role)
                house = 2
                wish_colour = (role and role.color) or discord.Colour.from_str("#FFD800")
            elif any(r.id == ravenclaw_role for r in birthday_member.roles):
                role = guild.get_role(ravenclaw_role)
                house = 3
                wish_colour = (role and role.color) or discord.Colour.from_str("#0E1A40")
            elif any(r.id == slytherin_role for r in birthday_member.roles):
                role = guild.get_role(slytherin_role)
                house = 4
                wish_colour = (role and role.color) or discord.Colour.from_str("#1A472A")
            else:
                role = guild.get_role(test_role)
                wish_colour = (role and role.color) or discord.Colour.blurple()
                house = random.randint(1,5)

            birthday_embed = discord.Embed(title=f"Happy Birthday {birthday_member.name}!", 
                description=await wish_creator(house, birthday_member.name), 
                colour=wish_colour)
            birthday_embed.set_thumbnail(url=avatar_url)
            birthday_embed.set_image(url=r"https://img.freepik.com/premium-photo/birthday-cake-magical-background-with-bokeh-sparkles-happy-birthday-greeting-card-design_174533-13977.jpg")
            channel = guild.get_channel(test_channel) or await guild.fetch_channel(test_channel)
            await channel.send(
                birthday_member.mention,
                embed=birthday_embed,
                allowed_mentions=discord.AllowedMentions(users=True),
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
    
    
    async def timezone_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=tz, value = tz)
            for tz in available_timezones()
            if current.lower() in tz.lower()
        ][:25]


    birthday_group = app_commands.Group(name="birthday", description = "birthday commands")


    @birthday_group.command(name="add", description="Add a birthday to the database")
    @app_commands.describe(
        user="Select a user or provide their ID",
        day="Their birthday day (1-31)",
        month="Their birthday month (1-12)",
        timezone="Their IANA timezone (e.g. 'America/New_York')",
    )
    @app_commands.autocomplete(timezone = timezone_autocomplete)
    @app_commands.checks.has_any_role(professors, goblins, poltergeists, test_role)
    async def birthday(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        day: int,
        month: int,
        timezone: str = "UTC",
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            ZoneInfo(timezone)
        except Exception:
            await interaction.followup.send(
                "Invalid timezone. Please select one from the autocomplete list.",
                ephemeral=True,
            )
            return
        db = await init_db()
        async with db.execute("SELECT 1 FROM birthdays WHERE user_id = ?", (user.id,)) as cur:
            row = await cur.fetchone()
        if row:
            await interaction.followup.send(
                f"{user.mention} already has a birthday entry. Use /birthday show to view.",
                ephemeral=True,
            )
            return
        try:
            await db.execute(
                "INSERT INTO birthdays (user_id, month, day, timezone) VALUES (?,?,?,?)",
                (user.id, month, day, timezone),
                )
            await db.commit()
            await interaction.followup.send(
                f"Added birthday for {user.mention} on {day}/{month} in timezone {timezone}.",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.followup.send(
                f"Error entering data, please check for mistakes and try again.\n{e}", 
                ephemeral=True)


    @birthday_group.command(name="edit", description="Edit an existing birthday entry")
    @app_commands.describe(
        user="select a user or provide their ID",
        day="Their birthday day (1-31)",
        month="Their birthday month (1-12)",
        timezone="Their IANA timezone (e.g. 'America/New_York')",
    )
    @app_commands.autocomplete(timezone=timezone_autocomplete)
    @app_commands.checks.has_any_role(professors, goblins, poltergeists, test_role)
    async def edit_birthday(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        day: int = None, 
        month: int = None, 
        timezone: str = None
        ):
        await interaction.response.defer(ephemeral=True)
        if timezone is not None:
            try:
                ZoneInfo(timezone)
            except Exception:
                await interaction.followup.send(
                    "Invalid timezone. Please select one from the autocomplete list.",
                    ephemeral=True,
                    )
                return

        if month is None and day is None and timezone is None:
            await interaction.followup.send(
                "No changes provided. Specify at least one of month, day, or timezone.",
                ephemeral=True,
                )
            return

        db = await init_db()
        async with db.execute("SELECT month, day, timezone FROM birthdays WHERE user_id = ?", (user.id,)) as cur:
            row = await cur.fetchone()
        if not row:
            await interaction.followup.send(
                f"{user.mention} does not have a birthday entry. Contact your nearest poltergeist to add one.",
                ephemeral=True,
                )
            return

        try:
            current_month, current_day, current_tz = row
            new_month = month if month is not None else current_month
            new_day = day if day is not None else current_day
            new_tz = timezone if timezone is not None else current_tz

            await db.execute(
                """
                UPDATE birthdays
                SET month = ?, day = ?, timezone = ?
                WHERE user_id = ?
                """,
                (new_month, new_day, new_tz, user.id),
                )
            await db.commit()

            await interaction.followup.send(
                f"Updated birthday for {user.mention} to {new_day}/{new_month} in timezone {new_tz}.",
                ephemeral=True,
                )
        except Exception as e:
            await interaction.followup.send(
                f"Error updating data. Please check for mistakes and try again.\n{e}", 
                ephemeral=True
                )


    @birthday_group.command(name="remove", description="Remove a birthday entry")
    @app_commands.describe(user="Select a user or provide their ID")
    @app_commands.checks.has_any_role(professors, goblins, poltergeists, test_role)
    async def remove_birthday(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
    ):
        await interaction.response.defer(ephemeral=True)
        db = await init_db()
        async with db.execute("SELECT 1 FROM birthdays WHERE user_id = ?", (user.id,)) as cur:
            row = await cur.fetchone()
        if not row:
            await interaction.followup.send(
                f"{user.mention} does not have a birthday entry. Contact your nearest poltergeist to add one.",
                ephemeral=True,
            )
            return
        await db.execute("DELETE FROM birthdays WHERE user_id = ?", (user.id,))
        await db.commit()
        await interaction.followup.send(
            f"Removed birthday entry for {user.mention}.",
            ephemeral=True,
        )


    @birthday_group.command(name="show", description="Show a user's birthday information")
    @app_commands.describe(user="Select a user or provide their ID")
    async def show_birthday(
        self,
        interaction: discord.Interaction, 
        user: discord.Member
    ):
        await interaction.response.defer()
        db = await init_db()
        async with db.execute("SELECT month, day FROM birthdays WHERE user_id = ?", (user.id,)) as cur:
            row  = await cur.fetchone()
            if row is None:
                entry_not_found_embed = discord.Embed(title="Entry not found",
                description=f"{user.mention} does not have a birthday entry. Contact your nearest poltergeist to add one.", 
                colour=discord.Colour.red())
                await interaction.followup.send(embed=entry_not_found_embed, allowed_mentions=discord.AllowedMentions(users=True))
                return
            month, day = row
            show_embed = discord.Embed(title=f"{user.name}'s Birthday", 
                description=f"{user.mention}'s birthday is on {day}/{month}.", 
                colour=discord.Colour.blurple())
            await interaction.followup.send(embed=show_embed, allowed_mentions=discord.AllowedMentions(users=True))


    @birthday_group.command(name="force", description="Force a wish checking cycle to run")
    @app_commands.checks.has_any_role(professors, goblins, test_role)
    async def force_wish(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            to_wish = await birthay_parser(self.bot)
            if to_wish:
                await self.wish_sender(to_wish)
        except Exception as e:
            print("error",e)
        await interaction.followup.send("Force wish cycle completed.", ephemeral=True)
            


async def setup(bot: commands.Bot):
    await init_db()
    cog = birthday_handling(bot)
    await bot.add_cog(cog)

    async def _start_loop():
        await bot.wait_until_ready()
        bot.loop.create_task(cog.wish_checker(bot))

    bot.loop.create_task(_start_loop())