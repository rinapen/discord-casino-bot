import asyncio
import datetime
from datetime import timedelta
import os
import random

import discord
from discord import app_commands
from discord.ext import commands, tasks
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import pytz

from bot import bot
from commands import register_all_text_commands
from config import GUILD_ID
import config
from paypay_session import paypay_session
from tasks.usage_ranking import send_monthly_usage_ranking, send_or_update_ranking
from utils.account_panel import setup_account_panel
from utils.invite_panel import check_invite_usage_diff, initialize_invite_cache, setup_invite_panel
from utils.pnc import get_daily_profit, get_total_pnc, get_total_revenue

JST = pytz.timezone("Asia/Tokyo")

@tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=JST))
async def daily_report_task():
    await send_daily_report()

@tasks.loop(seconds=60)
async def invite_monitor_loop():
    guild = bot.get_guild(GUILD_ID)
    if guild:
        try:
            await check_invite_usage_diff(guild)
            print("✅ Invite usage diff checked")
        except Exception as e:
            print(f"❌ Error during invite diff check: {e}")

async def send_daily_report(target_date: str = None):
    if target_date is None:
        now = datetime.datetime.now(JST)
        target_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    daily_profit = get_daily_profit(target_date)
    total_pnc = get_total_pnc()
    monthly_revenue = get_total_revenue()

    profit_rate = (daily_profit / total_pnc * 100) if total_pnc > 0 else 0.0

    channel = bot.get_channel(int(config.ADMIN_CHANNEL_ID))
    if channel:
        embed = discord.Embed(
            title="💰 カジノ収益レポート",
            description=f"**{target_date} のカジノ利益状況**",
            color=discord.Color.gold()
        )
        embed.add_field(name="📈 本日の利益", value=f"`{daily_profit:,} 円`", inline=False)
        embed.add_field(name="📊 利益率", value=f"`{profit_rate:.2f}%`", inline=False)
        embed.add_field(name="📅 総収益", value=f"`{monthly_revenue:,} 円`", inline=False)
        embed.add_field(name="💳 全ユーザー保有PNC", value=f"`{total_pnc:,} PNC`", inline=False)
        embed.set_footer(text="⏳ 自動送信 - カジノレポート")

        await channel.send(embed=embed)

        graph_path = create_monthly_profit_graph()
        file = discord.File(graph_path, filename="monthly_profit.png")
        graph_embed = discord.Embed(
            title="📊 直近30日間のカジノ利益推移",
            color=discord.Color.blurple()
        )
        graph_embed.set_image(url="attachment://monthly_profit.png")
        await channel.send(embed=graph_embed, file=file)

def create_monthly_profit_graph():
    REPORTS_DIR = "reports"
    os.makedirs(REPORTS_DIR, exist_ok=True)

    font_path = "assets/font/NotoSansJP-VariableFont_wght.ttf"
    jp_font = fm.FontProperties(fname=font_path)

    JST = datetime.datetime.now().astimezone().tzinfo
    today = datetime.datetime.now(JST)
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]
    profits = [get_daily_profit(date) for date in dates]

    plt.figure(figsize=(12, 6))
    plt.plot(dates, profits, marker='o', linestyle='-', color='blue')

    plt.title("📊 過去30日間のカジノ収益推移", fontproperties=jp_font)
    plt.xlabel("日付", fontproperties=jp_font)
    plt.ylabel("利益（円）", fontproperties=jp_font)
    plt.xticks(rotation=45, fontproperties=jp_font)
    plt.yticks(fontproperties=jp_font)
    plt.grid(True)

    for i, profit in enumerate(profits):
        plt.annotate(f"{profit:,}", (dates[i], profits[i]),
                     textcoords="offset points", xytext=(0, 8), ha='center', fontsize=8, fontproperties=jp_font)

    plt.tight_layout()
    image_path = os.path.join(REPORTS_DIR, "monthly_profit.png")
    plt.savefig(image_path, bbox_inches="tight")
    plt.close()
    return image_path

async def keep_alive():
    while True:
        await bot.wait_until_ready()
        print(f"✅ WebSocket is stable: {round(bot.latency * 1000)}ms")
        try:
            paypay_session.paypay.alive()
        except Exception as e:
            print(f"[ERROR] keep_alive error: {e}")
        sleep_time = random.randint(240, 420)
        await asyncio.sleep(sleep_time)

@bot.event
async def on_ready():
    print("[DEBUG] on_ready 実行開始")
    await bot.tree.sync()
    print(f"🟢 Logged in as {bot.user}")

    for guild in bot.guilds:
        if guild.id == GUILD_ID:
            try:
                await initialize_invite_cache(guild)
                print(f"✅ Initialized invite cache for {guild.name}")
            except Exception as e:
                print(f"❌ Failed to initialize invites for {guild.name}: {e}")

    await setup_account_panel()
    # await setup_invite_panel(bot)

    if not daily_report_task.is_running():
        daily_report_task.start()

    if not invite_monitor_loop.is_running():
        invite_monitor_loop.start()

    if not send_monthly_usage_ranking.is_running():
        send_monthly_usage_ranking.start()

    await send_or_update_ranking()
    try:
        await send_daily_report()
    except Exception as e:
        print(f"[ERROR] 起動時レポート送信エラー: {e}")
        error_embed = discord.Embed(
            title="⚠️ レポート送信エラー",
            description=f"Bot起動時にカジノ収益レポートの送信に失敗しました。\n`{type(e).__name__}: {str(e)}`",
            color=discord.Color.red()
        )
        error_channel = bot.get_channel(int(config.ADMIN_CHANNEL_ID))
        if error_channel:
            await error_channel.send(embed=error_embed)

async def main():
    asyncio.create_task(keep_alive())
    await register_all_text_commands(bot)
    await bot.start(config.TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 ボットの実行を中断しました。終了します。")