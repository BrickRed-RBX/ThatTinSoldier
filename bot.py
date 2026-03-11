# bot.py
import os
import random
import json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID")) if os.getenv("GUILD_ID") else None
STATE_FILE = "state.json"

# Intents: include message_content for legacy text commands (postnow), plus basic intents
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True  # privileged intent; enable in Developer Portal for your bot

bot = commands.Bot(command_prefix="!", intents=intents)
scheduler = AsyncIOScheduler()

# Load lines (one quote per line)
with open("lines.txt", encoding="utf-8") as f:
    LINES = [line.strip() for line in f if line.strip()]

# Default state
default_state = {
    "channel_id": None,
    "interval_seconds": 86400,
    "enabled": False
}

def load_state():
    if os.path.isfile(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                s = json.load(f)
                return {**default_state, **s}
        except Exception:
            return default_state.copy()
    return default_state.copy()

def save_state():
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)

state = load_state()

def pick_line():
    return random.choice(LINES) if LINES else "..."

async def send_line(channel_id):
    try:
        channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
    except Exception:
        return
    try:
        await channel.send(pick_line())
    except Exception:
        pass

async def scheduled_job():
    if state["enabled"] and state["channel_id"]:
        await send_line(state["channel_id"])

def reschedule():
    try:
        scheduler.remove_job("tin_soldier_job")
    except Exception:
        pass
    if state["enabled"] and state["channel_id"]:
        trigger = IntervalTrigger(seconds=state["interval_seconds"])
        # Fixed: Use datetime.now(timezone.utc) instead of deprecated datetime.utcnow()
        scheduler.add_job(
            scheduled_job, 
            trigger, 
            id="tin_soldier_job", 
            next_run_time=datetime.now(timezone.utc) + timedelta(seconds=1)
        )
    save_state()

def parse_unit_to_seconds(interval: int, unit: str):
    unit = unit.lower()
    if unit.startswith("min"):
        return max(60, interval * 60)
    if unit.startswith("hour"):
        return max(3600, interval * 3600)
    if unit.startswith("day"):
        return max(86400, interval * 86400)
    raise ValueError("Invalid unit")

def is_admin(member: discord.Member):
    return bool(member.guild_permissions.manage_guild)

class AdminSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Configure That Tin Soldier: channel and cooldown.")
    @app_commands.describe(channel="Channel where Tin Soldier will post", interval="Interval amount", unit="minute/hour/day or 'off' to disable")
    async def setup(self, interaction: discord.Interaction, channel: discord.TextChannel, interval: int = 1, unit: str = "day"):
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Command can only be used in a server.", ephemeral=True)
            return
        if not is_admin(interaction.user):
            await interaction.response.send_message("You must have Manage Server permission to use this command.", ephemeral=True)
            return

        unit = unit.lower()
        if unit == "off":
            state["enabled"] = False
            reschedule()
            await interaction.response.send_message("That Tin Soldier disabled.", ephemeral=True)
            return

        if interval < 1:
            await interaction.response.send_message("Interval must be >= 1.", ephemeral=True)
            return

        try:
            seconds = parse_unit_to_seconds(interval, unit)
        except ValueError:
            await interaction.response.send_message("Unit must be minute/hour/day or 'off'.", ephemeral=True)
            return

        state["channel_id"] = channel.id
        state["interval_seconds"] = seconds
        state["enabled"] = True
        reschedule()
        await interaction.response.send_message(f"That Tin Soldier set to post every {interval} {unit}(s) in {channel.mention}.", ephemeral=True)

    @app_commands.command(name="status", description="Show That Tin Soldier status.")
    async def status(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Command can only be used in a server.", ephemeral=True)
            return
        if not is_admin(interaction.user):
            await interaction.response.send_message("You must have Manage Server permission to use this command.", ephemeral=True)
            return

        if not state["channel_id"] or not state["enabled"]:
            await interaction.response.send_message("That Tin Soldier is disabled.", ephemeral=True)
            return
        cid = state["channel_id"]
        seconds = state["interval_seconds"]
        if seconds % 86400 == 0:
            desc = f"{seconds // 86400} day(s)"
        elif seconds % 3600 == 0:
            desc = f"{seconds // 3600} hour(s)"
        else:
            desc = f"{seconds // 60} minute(s)"
        await interaction.response.send_message(f"Posting every {desc} in <#{cid}>.", ephemeral=True)

# Optional: slash command to force-post (admin-only)
@app_commands.guild_only()
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.command(name="postnow", description="Force That Tin Soldier to post now (admin only).")
async def slash_postnow(interaction: discord.Interaction):
    if not state["channel_id"]:
        await interaction.response.send_message("Channel not set.", ephemeral=True)
        return
    await send_line(state["channel_id"])
    await interaction.response.send_message("Posted line.", ephemeral=True)

# Text command fallback (requires message_content intent) for admins
@bot.command(name="postnow")
@commands.guild_only()
async def postnow(ctx):
    if not is_admin(ctx.author):
        await ctx.send("You must have Manage Server permission to use this command.")
        return
    if state["channel_id"]:
        await send_line(state["channel_id"])
        await ctx.send("Posted line.")
    else:
        await ctx.send("Channel not set.")

# Fixed: Set up hook properly
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    
    # Add cogs and commands
    await bot.add_cog(AdminSetup(bot))
    bot.tree.add_command(slash_postnow)
    
    # Sync commands
    if GUILD_ID:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
    else:
        await bot.tree.sync()
    
    # Start scheduler if not running
    if not scheduler.running:
        scheduler.start()
    reschedule()

# Run the bot
if __name__ == "__main__":
    bot.run(TOKEN)
