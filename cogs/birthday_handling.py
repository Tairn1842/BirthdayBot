import aiosqlite, discord, asyncio
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, available_timezones
from main import BirthdayBot

guild_id = 524552788932558848

gryffindor_role = 524558749512499230
hufflepuff_role = 524558390316498944
ravenclaw_role = 524558868383137812
slytherin_role = 524558928898424833

gryffindor_cr = 1123316248093134848
hufflepuff_cr = 1123320556419293184
ravenclaw_cr = 1123313188633595994
slytherin_cr = 1123304982934999150

db_path = "bot.db"
db: aiosqlite.Connection | None = None

create_sql = """
CREATE TABLE IF NOT EXISTS birthdays (
    user_id INTEGER PRIMARY KEY,
    month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    day INTEGER NOT NULL CHECK (day BETWEEN 1 AND 31),
    timezone TEXT NOT NULL,
    last_posted TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_birthdays ON birthdays(timezone, month, day);
"""

async def init_db():
    global db
    if db is None:
        db = await aiosqlite.connect(db_path)
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA synchronous=NORMAL;")
        await db.executescript(create_sql)
        await db.commit()
    return db

def is_leap_year(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

async def birthay_parser(bot):
    """
    Compute today's birthdays using the SQLite DB, per timezone, and return user_ids to wish.
    - Only selects rows matching today in their tz and where last_posted != today.
    - Membership check is cache-only (guild.get_member) to avoid rate limits.
    - Does NOT update last_posted; call mark_sent() after sending.
    """
    global db
    if db is None:
        db = await init_db()

    global guild_id
    guild = bot.get_guild(guild_id) or await bot.fetch_guild(guild_id)

    utc_now = datetime.now(timezone.utc)

    tzs = []
    async with db.execute("SELECT DISTINCT timezone FROM birthdays") as cur:
        async for (tz,) in cur:
            tzs.append(tz)

    if not tzs:
        return []

    to_wish_candidates = []
    for tz in tzs:
        try:
            z = ZoneInfo(tz)
        except Exception:
            z = timezone.utc

        local_now = utc_now.astimezone(z)
        ly, lm, ld = local_now.year, local_now.month, local_now.day
        today_key = local_now.date().isoformat()

        q_month, q_day = (3, 1) if (lm == 3 and ld == 1 and not is_leap_year(ly)) else (lm, ld)

        async with db.execute(
            """
            SELECT user_id
            FROM birthdays
            WHERE timezone = ? AND month = ? AND day = ?
              AND (last_posted IS NULL OR last_posted = '' OR last_posted <> ?)
            """,
            (tz, q_month, q_day, today_key),
        ) as cur:
            async for (user_id,) in cur:
                to_wish_candidates.append(user_id)

    if not to_wish_candidates:
        return []

    to_wish = []
    for uid in to_wish_candidates:
        if guild.get_member(uid):
            to_wish.append(uid)
        else:
            try:
                await guild.get_member(uid)  or guild.fetch_member(uid)
                to_wish.append(uid)
            except discord.NotFound:
                await db.execute("DELETE FROM birthdays WHERE user_id = ?", (uid,))
            except (discord.Forbidden, discord.HTTPException):
                pass
    await db.commit()

    return to_wish

async def mark_sent(user_ids):
    """
    After sending wishes, mark last_posted for those users using their own local date.
    Batched into a single transaction.
    """
    if not user_ids:
        return
    global db
    if db is None:
        db = await init_db()

    utc_now = datetime.now(timezone.utc)

    qmarks = ",".join("?" for _ in user_ids)
    async with db.execute(
        f"SELECT user_id, timezone FROM birthdays WHERE user_id IN ({qmarks})",
        user_ids,
    ) as cur:
        rows = await cur.fetchall()

    for uid, tz in rows:
        try:
            z = ZoneInfo(tz)
        except Exception:
            z = timezone.utc
        today_key = utc_now.astimezone(z).date().isoformat()
        await db.execute(
            "UPDATE birthdays SET last_posted = ? WHERE user_id = ?",
            (today_key, uid),
        )
    await db.commit()


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
            await self.bot.get_channel(wish_channel).send(birthday_member.mention, 
            embed = birthday_embed, allowed_mentions=True)

        await mark_sent(to_wish)


    async def wish_checker(self, bot: BirthdayBot):
        while True:
            to_wish = await birthay_parser(bot)
            if to_wish:
                await self.wish_sender(to_wish)
            await asyncio.sleep(900)