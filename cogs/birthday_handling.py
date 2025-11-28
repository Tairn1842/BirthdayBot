import aiosqlite, discord, asyncio
from discord.ext import commands
from datetime import datetime, timezone
import numpy as np
from pathlib import Path
from zoneinfo import ZoneInfo
from .wish_generator import wish_creator
from .variables import *


db_path = "bot.db"
db: aiosqlite.Connection | None = None

create_sql = """
CREATE TABLE IF NOT EXISTS birthdays (
  user_id INTEGER PRIMARY KEY,
  month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
  day   INTEGER NOT NULL CHECK (day BETWEEN 1 AND 31),
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

def is_leap_year(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


async def birthday_parser(bot: discord.Client) -> list[int]:
    global db
    if db is None:
        db = await init_db()

    guild = bot.get_guild(guild_id) or await bot.fetch_guild(guild_id)
    utc_now = datetime.now(timezone.utc)

    tzs: list[str] = []
    async with db.execute("SELECT DISTINCT timezone FROM birthdays") as cur:
        async for (tz,) in cur:
            tzs.append(tz)

    if not tzs:
        return []

    to_wish_candidates: list[int] = []

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
              AND (last_posted IS NULL OR last_posted = '' OR last_posted != ?)
            """,
            (tz, q_month, q_day, today_key),
        ) as cur:
            async for (user_id,) in cur:
                to_wish_candidates.append(user_id)

    if not to_wish_candidates:
        return []

    to_wish: list[int] = []
    to_delete: list[int] = []

    for uid in to_wish_candidates:
        member = guild.get_member(uid)
        if not member:
            try:
                member = await guild.fetch_member(uid)
            except discord.NotFound:
                member = None
            except (discord.Forbidden, discord.HTTPException):
                member = None

        if member:
            to_wish.append(uid)
        else:
            to_delete.append(uid)

    if to_delete:
        qmarks = ",".join("?" for _ in to_delete)
        await db.execute(f"DELETE FROM birthdays WHERE user_id IN ({qmarks})", to_delete)

    await db.commit()
    return to_wish

async def mark_sent(user_ids: list[int]) -> None:
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


async def checkpoint_wal():
    global db
    if db is None:
        db = await init_db()
    await db.execute("PRAGMA wal_checkpoint(FULL);")
    await db.commit()


images_dir = Path(__file__).parent.parent / "images"

class birthday_handling(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot  = bot


    async def wish_sender(self, to_wish):
        try:

            guild = self.bot.get_guild(guild_id) or await self.bot.fetch_guild(guild_id)

            for i in to_wish:
                birthday_member = guild.get_member(i) or await guild.fetch_member(i)
                avatar_url = birthday_member.avatar.url

                birthday_embed = discord.Embed(title=f"Happy Birthday {birthday_member.name}!", 
                    description=await wish_creator(), 
                    colour=birthday_member.colour)
                birthday_embed.set_thumbnail(url=avatar_url)
                birthday_image_selector = np.random.choice(images)
                birthday_image_path = images_dir / f"{birthday_image_selector}"
                birthday_image_file = discord.File(birthday_image_path, filename=birthday_image_path.name)
                birthday_embed.set_image(url=f"attachment://{birthday_image_file.filename}")
                channel = guild.get_channel(clock_tower) or await guild.fetch_channel(clock_tower)
                await channel.send(
                    birthday_member.mention,
                    file=birthday_image_file,
                    embed=birthday_embed,
                    allowed_mentions=discord.AllowedMentions(users=True),
                )

            await mark_sent(to_wish)

        except Exception as e:
            guild = self.bot.get_guild(guild_id)
            error_channel = guild.get_channel(bot_testing)
            await error_channel.send(f"{alert_emoji} Wishing Error: \n{e}")


    async def wish_checker(self, bot: commands.Bot):
        while True:
            await checkpoint_wal()
            try:
                to_wish = await birthday_parser(bot)
                if to_wish:
                    await self.wish_sender(to_wish)
            except Exception:
                pass
            await asyncio.sleep(900)


async def setup(bot: commands.Bot):
    await init_db()
    cog = (birthday_handling(bot))
    await bot.add_cog(cog)

    async def _start_loop():
        await bot.wait_until_ready()
        bot.loop.create_task(cog.wish_checker(bot))

    bot.loop.create_task(_start_loop())