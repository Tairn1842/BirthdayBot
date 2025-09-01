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


class help_command(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @app_commands.command(name="help", description="Get help with the bot's mechanisms")
    @app_commands.checks.has_any_role(professors, server_staff)
    @app_commands.checks.cooldown(rate=1, per=15, key = lambda i: i.user.id)
    async def help_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        birthday_setting_info = discord.Embed(
            title="Registering Birthdays", 
            description=
            "The primary purpose of this bot is to register and hold a list of our members' birthdays.\n"
            "On the day of someone's birthday, around midnight in the appointed timezone, the bot will send a wish.\n"
            "Currently, the wishes will be sent to the Atrium channel, although this is due to change upon full release.\n"
            "Regarding timezones, the next page of this embed will tell you why we allow you to set your own timezone, and how to do so.\n", 
            color=interaction.user.colour
        )
        birthday_setting_info.set_footer(text="Page 1 of 4")

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
        timezone_info.set_footer(text="Page 2 of 4")

        group_info = discord.Embed(
            title="Command Group Information",
            description="You will notice that most commands have two words in their name; the first is the command group.\n"
            "These groups are used to identify the purpose of and access to the commands in them.\n"
            "The help command and those in the 'birthday' group are accessible to all staff members.\n"
            "The override commands exist for use in special cases and are exclusive to the professors.\n"
            "Lastly, the debug commands exist for testing, evaluation, and debugging, and are exclusive to the bot owner — Tairn.",
            colour=interaction.user.colour)
        group_info.set_footer(text="Page 3 of 4")

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
        command_list.set_footer(text="Page 4 of 4")

        help_pages_list = [birthday_setting_info, timezone_info, group_info, command_list]
        view = help_pages(user= interaction.user, embeds=help_pages_list)
        await interaction.followup.send(embed=help_pages_list[0], view = view)


async def setup(bot: commands.Bot):
    await bot.add_cog(help_command(bot))