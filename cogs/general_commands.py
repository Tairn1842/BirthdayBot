import discord, time
from discord import app_commands
from discord.ext import commands
from .variables import *


class help_pages(discord.ui.View):
    def __init__(self, user, embeds):
        super().__init__(timeout=None)
        self.user = user
        self.embeds = embeds
        self.current_page = 0

    @discord.ui.button(label="previous", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "This is not your help menu", ephemeral=True
            )
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
        else:
            await interaction.response.send_message("You're already on the first page.", ephemeral=True)

    @discord.ui.button(label="next", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "This is not your help menu", ephemeral=True
            )
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
        else:
            await interaction.response.send_message("You're already on the last page.", ephemeral=True)


class general_commands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check the bot's latency")
    @app_commands.checks.has_any_role(professors, goblins)
    async def ping_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        latency = self.bot.latency * 1000
        ping_embed = discord.Embed(
            title="Pong!",
            description=f"Latency: {latency: .2f} ms", 
            color=interaction.user.colour
        )
        await interaction.followup.send(embed=ping_embed)


    @app_commands.command(name="help", description="Get help with the bot's mechanisms")
    @app_commands.checks.has_any_role(professors, goblins, server_staff)
    @app_commands.checks.cooldown(rate=1, per=15, key = lambda i: i.user.id)
    async def help_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        timezone_info = discord.Embed(
            title="Timezone information",
            description=
            "The birthday bot will wish people by default at UTC time.\n"
            "However, for some people, this may be on the day before their birthday or well into the afternoon on the day of their birthday.\n"
            "Therefore, the bot gives you the option to set a timezone for your (or somebody else's) birthday.\n"
            "This is done by entering their timezone in the IANA format.\n"
            "This **usually** takes the from of Continent/CapitalCity, but it can vary for some countries.\n"
            "If you're unsure about your IANA timezone code, you can check it out here: https://datetime.app/iana-timezones",
            color=interaction.user.colour
        )
        timezone_info.set_footer(text="Page 2 of 3")

        command_list = discord.Embed(
            title="Help Menu", 
            description="A list of the bot's commands", 
            color=interaction.user.colour
        )
        for cmd in self.bot.tree.get_commands():
            if isinstance(cmd, app_commands.Group):
                for sub in cmd.commands:
                    command_list.add_field(
                        name=f"{cmd.name} {sub.name}",
                        value=sub.description or "No description available",
                        inline=False,
                    )
            else:
                command_list.add_field(
                name=cmd.name, 
                value=cmd.description or "No description available", 
                inline=False
                )
        command_list.set_footer(text="Page 3 of 3")
        
        birthday_setting_info = discord.Embed(
            title="Registering Birthdays", 
            description=
            "The primary purpose of this bot is to register and hold a list of our members' birthdays.\n"
            "On the day of someone's birthday, around midnight in the appointed timezone, the bot will send a wish.\n"
            "Currently, the wishes will be sent to the Atrium channel, although this is due to change upon full release.\n"
            "Regarding timezones, the next page of this embed will tell you why we allow you to set your own timezone, and how to do so.\n"
            "The page after contains a list of the bot's commands.\n"
            "Most commands are currently accessible to all staff members. They have a 15-second cooldown so don't spam.\n"
            "Override commands are restricted to Goblins and Professors and exist primarily for testing, evaluation, and debugging.", 
            color=interaction.user.colour
        )
        birthday_setting_info.set_footer(text="Page 1 of 3")

        help_pages_list = [birthday_setting_info, timezone_info, command_list]
        view = help_pages(user= interaction.user, embeds=help_pages_list)
        await interaction.followup.send(embed=help_pages_list[0], view = view)


    @commands.command()
    @commands.has_any_role(goblins, professors)
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
        if isinstance(error, commands.BotMissingAnyRole):
            await ctx.send(
                "You do not have permission to use this command."
            )
        else:
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(general_commands(bot))