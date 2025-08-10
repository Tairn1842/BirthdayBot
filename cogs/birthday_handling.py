import aiosqlite
from typing import List, Tuple
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, available_timezones
import importlib
import discord

guild_id = 524552788932558848


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


async def birthay_parser(bot: discord.Client) -> list[int]:
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


_TIMEZONES: List[str] | None = None
_TIMEZONES_LC: List[str] | None = None

def _init_timezones() -> None:
    global _TIMEZONES, _TIMEZONES_LC
    if _TIMEZONES is not None:
        return

    try:
        tzs = available_timezones()
    except Exception:
        tzs = set()

    if not tzs:
        try:
            importlib.import_module("tzdata")
            tzs = available_timezones()
        except Exception:
            tzs = set()

    if not tzs:
        tzs = {
            "UTC",
            "Europe/London",
            "Europe/Paris",
            "America/New_York",
            "America/Los_Angeles",
            "Asia/Kolkata",
            "Asia/Tokyo",
            "Asia/Singapore",
            "Australia/Sydney",
        }

    keep = [
        z for z in tzs
        if ("/" in z or z == "UTC")
        and not z.startswith(("Etc/", "SystemV/", "Right/", "posix/", "US/", "Canada/", "Mexico/", "Brazil/", "Chile/"))
    ]
    keep = sorted(set(keep))
    if "UTC" in keep:
        keep.remove("UTC")
        keep.insert(0, "UTC")

    _TIMEZONES = keep
    _TIMEZONES_LC = [z.lower() for z in keep]

async def build_timezone_choices(current: str) -> List[Tuple[str, str]]:
    if _TIMEZONES is None:
        _init_timezones()

    tzs = _TIMEZONES or []
    tzs_lc = _TIMEZONES_LC or []

    q = (current or "").strip().lower()
    if not q:
        return [(z.replace("_", " "), z) for z in tzs[:25]]

    scored = []
    for z, zlc in zip(tzs, tzs_lc):
        if zlc.startswith(q):
            scored.append((0, z))
        else:
            city = zlc.split("/")[-1]
            if city.startswith(q):
                scored.append((1, z))
            elif q in zlc:
                scored.append((2, z))
    scored.sort(key=lambda x: (x[0], x[1]))
    top = [z for _, z in scored[:25]]
    return [(z.replace("_", " "), z) for z in top]