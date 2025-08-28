import discord, os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv


load_dotenv()
intents = discord.Intents.all()


class BirthdayBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='b!', intents = intents, help_command=None)

    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and not filename.startswith("__"):
                await self.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded cog: {filename}")


bot = BirthdayBot()


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingAnyRole):
        message = "You can't execute this command."
    elif isinstance(error, app_commands.CommandOnCooldown):
        message = "This command is on cooldown! Try again later!"
    elif isinstance(error, app_commands.NoPrivateMessage):
        message  = "You can't use this bot in DMs!"
    else:
        message = f"An unexpected error occured. Please alert the bot owner.\n{error}"
        guild = bot.get_guild(524552788932558848) or await bot.fetch_guild(524552788932558848)
        error_logging_channel = guild.get_channel(1068409137605656676) or await guild.fetch_channel(1068409137605656676)
        await error_logging_channel.send(f"Error executing {interaction.command.name}:\n{error}\nUser:{interaction.user.name}")

    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")


if __name__ == "__main__":
    bot.run(os.getenv("pottercord_birthday_bot_token"))