import discord, os, csv
from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()
intents = discord.Intents.all()


class BirthdayBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='b!', intents = intents, help_command=None)

    async def csv_writer(self):
        if not os.path.exists("birthdays.csv"):
            with open("birthdays.csv", "w", newline="") as file:
                list_writer = csv.writer(file)
                list_writer.writerow(["user_id", "birthday"])

        else:
            with open("birthdays.csv", "a", newline="") as file:
                list_writer = csv.writer(file)

    async def csv_reader(self):
        if os.path.exists("birthdays.csv"):
            with open("birthdays.csv","r", newline="") as file:
                list_reader = csv.reader(file)
    
    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and not filename.startswith("__"):
                await self.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded cog: {filename}")


bot = BirthdayBot()
async def on_ready():
    print(f"Logged in as {bot.user}")


if __name__ == "__main__":
    bot.run(os.getenv("bot_token"))