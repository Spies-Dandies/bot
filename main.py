import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = False  # Not needed if no message commands

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}.")

async def setup_hook():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

bot.setup_hook = setup_hook

TOKEN = os.environ.get("DISCORD_TOKEN")

bot.run(TOKEN)
