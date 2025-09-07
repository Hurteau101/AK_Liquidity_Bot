import os
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands
from sqlalchemy import create_engine
import pandas as pd


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

    @commands.command()
    async def csv(self, ctx):
        msg = await ctx.send("Generating Novig Excel File, please wait...")
        df = pd.read_sql(
            'SELECT snapshot_time AS "snapshot", player_name as "Player Name", '
            'stat_type as "Stat Type", line as "Line", game_title as "Game Title", '
            'total_over_liquidity as "Total Over Liquidity", '
            'total_under_liquidity as "Total Under Liqudity", '
            'highest_order_side as "Highest Order Side", '
            'odds_highest_order as "Hights Order Odds", '
            'liquidity_difference as "Liqudity Difference", '
            'league as "League" FROM novig_tracking',
            self.engine
        )
        df["snapshot"] = df["snapshot"].dt.tz_localize(None)
        file_path = "novig_tracking.xlsx"
        df.to_excel(file_path, index=False)

        await msg.edit(content="Novig Excel File Ready")
        await ctx.send(file=discord.File(file_path))


load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


async def setup_bot():
    await bot.add_cog(CSV_Bot(bot))
    await bot.start(os.getenv("DISCORD_BOT_TOKEN"))


if __name__ == "__main__":
    asyncio.run(setup_bot())
