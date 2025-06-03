import discord
from discord.ext import commands
import json
import os

class VoiceLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.counters_file = os.path.join(os.path.dirname(__file__), "..", "counters.json")
        if not os.path.exists(self.counters_file):
            with open(self.counters_file, "w") as f:
                json.dump({"users": {}}, f)

    def load_counters(self):
        with open(self.counters_file, "r") as f:
            return json.load(f)

    def save_counters(self, data):
        with open(self.counters_file, "w") as f:
            json.dump(data, f, indent=4)

    def ensure_user(self, data, user):
        user_id = str(user.id)
        if user_id not in data["users"]:
            data["users"][user_id] = {
                "name": str(user),
                "joins": 0,
                "leaves": 0,
                "moves": 0
            }
        else:
            data["users"][user_id]["name"] = str(user)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        log_channel_id = int(os.environ.get("LOG_CHANNEL_ID"))
        log_channel = self.bot.get_channel(log_channel_id)
        if log_channel is None:
            return

        data = self.load_counters()
        self.ensure_user(data, member)
        user_id = str(member.id)

        embed = discord.Embed(timestamp=discord.utils.utcnow())

        if before.channel is None and after.channel is not None:
            data["users"][user_id]["joins"] += 1
            embed.color = discord.Color.green()
            embed.description = f"<@{member.id}> has joined <#{after.channel.id}>"

        elif before.channel is not None and after.channel is None:
            data["users"][user_id]["leaves"] += 1
            embed.color = discord.Color.red()
            embed.description = f"<@{member.id}> has left <#{before.channel.id}>"

        elif before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
            data["users"][user_id]["moves"] += 1
            embed.color = discord.Color.orange()
            embed.description = (f"<@{member.id}> has moved from <#{before.channel.id}> "
                                 f"to <#{after.channel.id}>")
        else:
            return

        self.save_counters(data)
        await log_channel.send(embed=embed)

    @commands.slash_command(name="stats", description="Show voice channel stats")
    async def stats(self, ctx, user: discord.Option(str, "User ID or 'global'", required=False, choices=["global"]) = "global"):
        data = self.load_counters()
        embed = discord.Embed(title="Voice Channel Stats")

        if user == "global":
            joins = sum(u["joins"] for u in data["users"].values())
            leaves = sum(u["leaves"] for u in data["users"].values())
            moves = sum(u["moves"] for u in data["users"].values())
        else:
            joins = data["users"].get(user, {}).get("joins", 0)
            leaves = data["users"].get(user, {}).get("leaves", 0)
            moves = data["users"].get(user, {}).get("moves", 0)

        embed.description = (
            f"🟢 Joins: {joins}\n"
            f"🔴 Leaves: {leaves}\n"
            f"🟠 Moves: {moves}"
        )
        await ctx.respond(embed=embed)

    @commands.slash_command(name="counter-change", description="Modify voice counters")
    async def counter_change(self, ctx,
                             user: discord.Option(str, "User ID", required=True),
                             counter_type: discord.Option(str, "Counter type", required=True, choices=["joins", "leaves", "moves"]),
                             value: discord.Option(int, "New value", required=True)):
        data = self.load_counters()
        if user not in data["users"]:
            await ctx.respond(f"User {user} not tracked.", ephemeral=True)
            return

        data["users"][user][counter_type] = value
        self.save_counters(data)
        await ctx.respond(f"{counter_type} for user {user} set to {value}.")

def setup(bot):
    bot.add_cog(VoiceLogger(bot))
