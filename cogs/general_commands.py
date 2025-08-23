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


    @app_commands.command(name="help", description="Get help with the bot's commands")
    @app_commands.checks.has_any_role(professors, goblins, server_staff)
    @app_commands.checks.cooldown(rate=1, per=15, key = lambda i: i.user.id)
    async def help_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
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
        command_list.set_footer(text="Page 2 of 2")
        
        birthday_setting_info = discord.Embed(
            title="Registering Birthdays", 
            description=
            "The primary purpose of this bot is to register and hold a list of our members' birthdays.\n"
            "The next page of this embed contains a list of commands for you to use to that end.\n"
            "Most commands are currently accessible to all staff members."
            "Override commands are restricted to Goblins and Professors.\n\n"
            "Part of registering a birthday is setting a timezone.\n"
            "The timezone field is optional and the value defaults to UTC.\n"
            "But if the you (or another member) wishes to receive their wishes closer to **their** midnight, you'll need to set a timezone.\n"
            "Timezones are set in the IANA timezone format. (usually, continent/capital_city)\n"
            "You can find the IANA code at https://datetime.app/iana-timezones"
, 
            color=interaction.user.colour
        )
        birthday_setting_info.set_footer(text="Page 1 of 2")

        help_pages_list = [birthday_setting_info, command_list]
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