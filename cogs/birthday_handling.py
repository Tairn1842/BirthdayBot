import discord, csv, time
from discord.ext import commands
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, available_timezones
from main import BirthdayBot


def is_leap_year(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


file_path = "birthday_list.csv"
gryffindor_role = 524558749512499230
hufflepuff_role = 524558390316498944
ravenclaw_role = 524558868383137812
slytherin_role = 524558928898424833

gryffindor_cr = 1123316248093134848
hufflepuff_cr = 1123320556419293184
ravenclaw_cr = 1123313188633595994
slytherin_cr = 1123304982934999150


async def birthay_parser(bot):
    guild = bot.get_guild(524552788932558848)
    kept_rows = []
    todays_birthdays = []
    utc_now = datetime.now(timezone.utc)
    with open (file_path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                user_id = int(row["user_id"])
                month = int(row["month"])
                day = int(row["day"])
            except Exception as e:
                print(f"Error parsing row {row}: {e}")
                continue

            tz = (row.get("timezone") or "UTC").strip()
            last_posted  = row.get("last_posted", "").strip()
            kept_rows.append({'user_id': user_id, 
                              'month': month, 
                              'day': day, 
                              'timezone': tz, 
                              'last_posted': last_posted})
            try:
                z = ZoneInfo(tz)
            except Exception as e:
                print(f"Invalid timezone {tz} for user {user_id}: {e}")
                z = timezone.utc

            local_now = utc_now.astimezone(z)
            lm, ld, ly = local_now.month, local_now.day, local_now.year

            if month == 2 and day == 29 and not is_leap_year(ly):
                bday_matches = (lm == 3 and ld == 1)
            else:
                bday_matches = (lm == month and ld == day)

            if not bday_matches:
                continue

            today = local_now.date().isoformat()
            if last_posted and last_posted == today:
                continue

            todays_birthdays.append(user_id)


    if not todays_birthdays:
        return todays_birthdays

    to_prune: set[int] = set()
    to_wish: list[int] = []

    for uid in todays_birthdays:
        member = guild.get_member(uid)
        if member:
            to_wish.append(uid)
            continue

        try:
            member = await guild.fetch_member(uid)
        except discord.NotFound:
            member = None
        except (discord.Forbidden, discord.HTTPException):
            continue

        if member:
            to_wish.append(uid)
        else:
            to_prune.add(uid)

    if to_prune:
        kept_rows = [r for r in kept_rows if r["user_id"] not in to_prune]

    with open(file_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = ["user_id", "month", "day", "timezone", "last_posted"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in kept_rows:
            writer.writerow({
                "user_id": r["user_id"],
                "month": r["month"],
                "day": r["day"],
                "timezone": r["timezone"],
                "last_posted": r.get("last_posted", ""),
            })

    return to_wish

class birthday_handling(commands.Cog):
    def __init__(self, bot: BirthdayBot):
        self.bot = bot

    async def wish_sender(self, to_wish):
        guild = self.bot.get_guild(524552788932558848)
        for i in to_wish:
            birthday_member  = self.bot.get_user(i)
            if (role.id for role in birthday_member.roles) == gryffindor_role:
                wish_channel = gryffindor_cr
                wish_colour = guild.get_role(gryffindor_role).color
            elif (role.id for role in birthday_member.roles) == hufflepuff_role:
                wish_channel = hufflepuff_cr
                wish_colour = guild.get_role(hufflepuff_role).color
            elif (role.id for role in birthday_member.roles) == ravenclaw_role:
                wish_channel = ravenclaw_cr
                wish_colour = guild.get_role(ravenclaw_role).color
            elif (role.id for role in birthday_member.roles) == slytherin_role:
                wish_channel = slytherin_cr
                wish_colour = guild.get_role(slytherin_role).color

            
            birthday_embed = discord.Embed() # build embed upon decision
            await self.bot.get_channel(wish_channel).send(birthday_member.mention, embed = birthday_embed, allowed_mentions=True)