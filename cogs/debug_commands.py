import discord, time
from discord import app_commands
from discord.ext import commands
from .birthday_handling import *
from .variables import *


def owner_check():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id == tairneanach:
            return True
        return False
    return app_commands.check(predicate=predicate)


@owner_check()
class debug_commands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.months_list=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    
    debug_group = app_commands.Group(name="debug", description="debugging and evaluation commands exclusive to the bot owner.")


    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context):
        start_time = time.time()
        try:
            synced = await self.bot.tree.sync()
            end_time = time.time()
            duration = end_time - start_time
            await ctx.send(
                f"Synced {len(synced)} commands globally in {duration:.2f} seconds."
            )
        except discord.HTTPException as e:
            await ctx.send(f"Error while syncing: {str(e)}")
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.NotOwner):
            await ctx.send(
                "You do not have permission to use this command."
            )
        else:
            raise error


    @debug_group.command(name="force", description="Force a wish checking cycle to run")
    @owner_check()
    async def force_wish(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        handling_cog = self.bot.get_cog("birthday_handling")
        to_wish = await birthday_parser(self.bot)
        if to_wish:
            await handling_cog.wish_sender(to_wish)
        await interaction.followup.send("Force wish cycle completed.")
    

    @debug_group.command(name="status", description="Displays the nearest (registered) birthdays and the size of the database")
    @owner_check()
    async def db_status(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        db = await init_db()
        guild = self.bot.get_guild(guild_id) or await self.bot.fetch_guild(guild_id)
        status_embed = discord.Embed(title="Database status information", 
                                     description="The nearest (registered) birthdays and the size of the database:",
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
    

    @debug_group.command(name="ping", description="Check the bot's latency")
    @owner_check()
    async def ping_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        latency = self.bot.latency * 1000
        ping_embed = discord.Embed(
            title="Pong!",
            description=f"Latency: {latency: .2f} ms", 
            color=interaction.user.colour
        )
        await interaction.followup.send(embed=ping_embed)


async def setup(bot: commands.Bot):
    await init_db()
    cog = debug_commands(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.debug_group)
    except app_commands.CommandAlreadyRegistered:
        pass