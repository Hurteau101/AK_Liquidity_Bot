import os
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands
from sqlalchemy import create_engine
import pandas as pd
from discord import app_commands

class CSV_Bot(commands.Cog):
    def __init__(self, bot):
        load_dotenv()
        self.bot = bot
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASS")
        self.host = os.getenv("DB_HOST")
        self.port = os.getenv("DB_PORT")
        self.database = os.getenv("DB_NAME")

        self.engine = create_engine(
            f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        )

    # @commands.command()
    # async def csv(self, ctx):
    #     msg = await ctx.send("Generating Novig_Dir Excel File, please wait...")
    #     df = pd.read_sql(
    #         'SELECT snapshot_time AS "snapshot", player_name as "Player Name", '
    #         'game_start_time as "Game Start Time",'
    #         'stat_type as "Stat Type", line as "Line", game_title as "Game Title", '
    #         'total_over_liquidity as "Total Over Liquidity", '
    #         'total_under_liquidity as "Total Under Liqudity", '
    #         'highest_order_side as "Highest Order Side", '
    #         'liquidity_highest_order as "Highest Order Liquidity", '
    #         'odds_highest_order as "Hights Order Odds", '
    #         'liquidity_difference as "Liqudity Difference", '
    #         'league as "League",'
    #         'over_result as "Over Result",'
    #         'under_result as "Under Result" FROM novig_tracking',
    #
    #         self.engine
    #     )
    #
    #     df["snapshot"] = df["snapshot"].dt.tz_localize(None)
    #     df["Game Start Time"] = df["Game Start Time"].dt.tz_localize(None)
    #     file_path = "novig_tracking.xlsx"
    #     df.to_excel(file_path, index=False)
    #
    #     await msg.edit(content="Novig_Dir Excel File Ready")
    #     await ctx.send(file=discord.File(file_path))

    @app_commands.command(name="csv", description="Generate an Excel file for a specific league.")
    @app_commands.describe(league="The league you want to export data for (e.g. NBA, NFL, etc.)")
    async def csv(self, interaction: discord.Interaction, league: str):
        league = league.upper()

        await interaction.response.send_message(f"Generating Excel file for **{league}**, please wait...",
                                                ephemeral=True)

        # Query filtered by league
        query = f"""
           SELECT snapshot_time AS "Snapshot",
                  player_name AS "Player Name",
                  game_start_time AS "Game Start Time",
                  stat_type AS "Stat Type",
                  line AS "Line",
                  game_title AS "Game Title",
                  total_over_liquidity AS "Total Over Liquidity",
                  total_under_liquidity AS "Total Under Liquidity",
                  highest_order_side AS "Highest Order Side",
                  liquidity_highest_order AS "Highest Order Liquidity",
                  odds_highest_order AS "Highest Order Odds",
                  liquidity_difference AS "Liquidity Difference",
                  league AS "League",
                  over_result AS "Over Result",
                  under_result AS "Under Result"
           FROM novig_tracking
           WHERE league = '{league}'
           """

        df = pd.read_sql(query, self.engine)

        if df.empty:
            await interaction.followup.send(f"No data found for league `{league}`.")
            return

        df["Snapshot"] = df["Snapshot"].dt.tz_localize(None)
        df["Game Start Time"] = df["Game Start Time"].dt.tz_localize(None)

        file_path = f"novig_tracking_{league}.xlsx"
        df.to_excel(file_path, index=False)

        await interaction.followup.send(
            f"Excel file for **{league}** is ready:",
            file=discord.File(file_path)
        )


load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()  # ✅ This is what registers /csv
        print("✅ Slash commands synced with Discord!")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
    print(f"🤖 Logged in as {bot.user}")


async def setup_bot():
    await bot.add_cog(CSV_Bot(bot))
    await bot.start(os.getenv("DISCORD_BOT_TOKEN"))


if __name__ == "__main__":
    asyncio.run(setup_bot())
