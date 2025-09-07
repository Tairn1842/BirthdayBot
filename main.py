import discord, os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import datetime as dt


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

    async def on_message(self, message: discord.Message):
        if isinstance(message.channel, discord.DMChannel):
            if not message.author.bot:
                await message.reply("You can't use the bot here.", delete_after=5)
                pass
        else:
            await bot.process_commands(message)


bot = BirthdayBot()


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingAnyRole):
        message = "You can't execute this command."
    elif isinstance(error, app_commands.CommandOnCooldown):
        now_ts  = dt.datetime.now(dt.timezone.utc).timestamp()
        message = f"This command is on cooldown! Try again <t:{int(now_ts+error.retry_after)}:R>."
    elif isinstance(error, app_commands.CheckFailure):
        message = "You do not have permission to use this command."
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
    try:
        bot.tree.allowed_contexts = app_commands.AppCommandContext(guild=True, private_channel=False, dm_channel=False)
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands globally.")
    except discord.HTTPException as e:
        print(f"Error while syncing: {str(e)}")


if __name__ == "__main__":
    bot.run(os.getenv("pottercord_birthday_bot_token"))