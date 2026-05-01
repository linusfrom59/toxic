import os
import random
import sys
from pathlib import Path

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
load_dotenv(project_root / '.env')

from database.db import init_db, link_discord_account, get_submission, get_unannounced_submissions, mark_submission_announced, get_recent_submission_ids

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


def parse_channel_id(value):
    if not value or not value.isdigit():
        return None
    return int(value)


WELCOME_CHANNEL_ID = parse_channel_id(os.getenv("WELCOME_CHANNEL_ID"))
PANEL_CHANNEL_ID = parse_channel_id(os.getenv("PANEL_CHANNEL_ID"))
ADMIN_CHANNEL_ID = parse_channel_id(os.getenv("ADMIN_CHANNEL_ID"))
ADMIN_CHANNEL_NAME = os.getenv("ADMIN_CHANNEL_NAME", "verification lvl.5")
VERIFICATION_CHANNEL_NAME = os.getenv("VERIFICATION_CHANNEL_NAME", "verification lvl.5")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://deine-domain.de")

welcome_messages = [
    "Welcome to Toxic! Ready to brawl and dominate the arena? 💀🔥",
    "A new brawler has joined Toxic! Let’s climb trophies together! 🏆",
    "Welcome to Toxic Club! Time to show your Brawl Stars skills! 🎮",
    "Another fighter enters Toxic! Let the chaos begin! ⚡",
    "Welcome to Toxic! Stay toxic, play smart, and win big! 💥",
    "A new challenger appears in Toxic! Ready for battle? 🔫",
    "Welcome to Toxic Club! Let’s push trophies and destroy enemies! 🏆🔥",
    "Toxic just got stronger! Welcome and let’s brawl! 💀",
    "Welcome to Toxic! May your aim be sharp and your wins legendary! 🎯",
    "A new legend joins Toxic! Let’s dominate Brawl Stars together! 👑"
]


class WebsitePanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label="Open Website",
                style=discord.ButtonStyle.link,
                url=WEBSITE_URL,
                emoji="🌐",
            )
        )


class SubmissionDetailsView(discord.ui.View):
    def __init__(self, submission_id: int):
        super().__init__(timeout=None)
        self.add_item(SubmissionDetailsButton(submission_id))


class SubmissionDetailsButton(discord.ui.Button):
    def __init__(self, submission_id: int):
        super().__init__(
            label="View details",
            style=discord.ButtonStyle.primary,
            custom_id=f"submission_details:{submission_id}",
        )
        self.submission_id = submission_id

    async def callback(self, interaction: discord.Interaction):
        row = get_submission(self.submission_id)
        if row is None:
            await interaction.response.send_message("This submission no longer exists.", ephemeral=True)
            return

        embed = discord.Embed(
            title=row["ingame_name"],
            description="Verification details",
        )
        embed.add_field(name="Age", value=row["age_group"] or "-", inline=True)
        embed.add_field(name="Country", value=row["country"] or "-", inline=True)
        embed.add_field(name="Highest Rank", value=row["highest_rank"] or "-", inline=True)
        embed.add_field(name="Highest Trophies", value=row["highest_trophies"] or "-", inline=True)
        embed.add_field(name="Club Member", value=row["club_member"] or "-", inline=True)
        embed.add_field(name="Link Code", value=row["link_code"] or "-", inline=True)
        embed.add_field(name="Privacy Opened", value=row["privacy_opened"] or "false", inline=True)
        embed.add_field(name="Privacy Scrolled", value=row["privacy_scrolled"] or "false", inline=True)

        if row["profile_image"]:
            image_url = f"{WEBSITE_URL.rstrip('/')}/static/uploads/{row['profile_image']}"
            embed.set_image(url=image_url)

        await interaction.response.send_message(embed=embed, ephemeral=True)


def get_admin_channel(guild=None):
    if ADMIN_CHANNEL_ID:
        channel = bot.get_channel(ADMIN_CHANNEL_ID)
        if channel:
            return channel

    guilds = [guild] if guild else bot.guilds
    for current_guild in guilds:
        if current_guild is None:
            continue
        channel = discord.utils.get(current_guild.text_channels, name=ADMIN_CHANNEL_NAME)
        if channel:
            return channel
    return None


async def send_submission_to_admin_channel(row):
    channel = get_admin_channel()
    if channel is None:
        return

    await channel.send(
        content=row["ingame_name"],
        view=SubmissionDetailsView(row["id"]),
        allowed_mentions=discord.AllowedMentions.none(),
    )
    mark_submission_announced, get_recent_submission_ids(row["id"])


@tasks.loop(seconds=10)
async def announce_new_submissions():
    for row in get_unannounced_submissions():
        await send_submission_to_admin_channel(row)


@announce_new_submissions.before_loop
async def before_announce_new_submissions():
    await bot.wait_until_ready()


def get_verification_channel(guild=None):
    if PANEL_CHANNEL_ID:
        channel = bot.get_channel(PANEL_CHANNEL_ID)
        if channel:
            return channel

    guilds = [guild] if guild else bot.guilds
    for current_guild in guilds:
        if current_guild is None:
            continue
        channel = discord.utils.get(current_guild.text_channels, name=VERIFICATION_CHANNEL_NAME)
        if channel:
            return channel
    return None


async def send_website_panel(channel):
    embed = discord.Embed(
        title="Verification",
        description="Click the button below to open the website and start your verification.",
    )
    await channel.send(embed=embed, view=WebsitePanelView())


async def ensure_website_panel(channel):
    async for message in channel.history(limit=25):
        if message.author == bot.user and message.embeds:
            if message.embeds[0].title == "Verification":
                return
    await send_website_panel(channel)


@bot.event
async def on_ready():
    init_db()
    bot.add_view(WebsitePanelView())
    for submission_id in get_recent_submission_ids(limit=100):
        bot.add_view(SubmissionDetailsView(submission_id))
    if not announce_new_submissions.is_running():
        announce_new_submissions.start()
    channel = get_verification_channel()
    if channel:
        await ensure_website_panel(channel)
    print(f"Bot is online as {bot.user}")


@bot.event
async def on_member_join(member: discord.Member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID) if WELCOME_CHANNEL_ID else None
    if channel:
        await channel.send(f"{member.mention} {random.choice(welcome_messages)}")


@bot.command(name="link")
async def link(ctx: commands.Context, link_code: str):
    success = link_discord_account(link_code.strip().upper(), ctx.author.id)

    if success:
        await ctx.reply(
            "Your website form was successfully linked to your Discord account. ✅",
            mention_author=False,
        )
    else:
        await ctx.reply(
            "Invalid or already used link code. Please check the code from the website.",
            mention_author=False,
        )


@bot.command(name="panel")
@commands.has_permissions(administrator=True)
async def panel(ctx: commands.Context):
    panel_channel = get_verification_channel(ctx.guild)
    if panel_channel is None:
        await ctx.reply("Verification channel not found.", mention_author=False)
        return

    await send_website_panel(panel_channel)
    await ctx.reply("Panel sent. ✅", mention_author=False)


@panel.error
async def panel_error(ctx: commands.Context, error: Exception):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("You need administrator permissions for this.", mention_author=False)
        return
    raise error


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN is missing in the .env file")
    bot.run(DISCORD_TOKEN)
